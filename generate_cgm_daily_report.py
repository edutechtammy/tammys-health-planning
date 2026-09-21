#!/usr/bin/env python3
"""
Generate a styled daily CGM PNG report from CSV data.

Supports two data sources:
1) --csv path/to/file.csv
2) Embedded `csvData` inside cgm-tracker.html (fallback when --csv is omitted)

Output styling is aligned to existing cycle report images, including:
- target range shading
- in-range/high markers
- daily metrics summary
- clinical diary logs & notes block
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


@dataclass
class CgmPoint:
    ts: datetime
    glucose: float


@dataclass
class SpikeEvent:
    onset: datetime
    peak_time: datetime
    peak_value: float
    duration_minutes: int


def parse_timestamp(value: str) -> datetime:
    raw = value.strip()
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        # Lingo exports sometimes omit seconds, e.g. 2026-06-07T23:09-05:00.
        m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})([+-]\d{2}:\d{2})$", raw)
        if m:
            normalized = f"{m.group(1)}:00{m.group(2)}"
            return datetime.fromisoformat(normalized)
        m_no_tz = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})$", raw)
        if m_no_tz:
            return datetime.fromisoformat(f"{raw}:00")
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a daily CGM report PNG from cumulative CSV data."
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Target date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--csv",
        help="Path to source CSV. If omitted, attempts to use embedded csvData from --preset-html.",
    )
    parser.add_argument(
        "--preset-html",
        default="cgm-tracker.html",
        help="HTML file containing embedded PRESET_CYCLE csvData template literal.",
    )
    parser.add_argument(
        "--output",
        help="Output PNG path. Default: cgm_report_YYYY-MM-DD.png",
    )
    parser.add_argument(
        "--target-low",
        type=float,
        default=70.0,
        help="Lower target range threshold (mg/dL).",
    )
    parser.add_argument(
        "--target-high",
        type=float,
        default=140.0,
        help="Upper target range threshold (mg/dL).",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Additional clinical note line(s). Can be passed multiple times.",
    )
    parser.add_argument(
        "--no-auto-spike-note",
        action="store_true",
        help="Disable automatic glycemic spike note generation.",
    )
    return parser.parse_args()


def load_csv_text(csv_path: str | None, preset_html_path: str) -> str:
    if csv_path:
        return Path(csv_path).read_text(encoding="utf-8")

    html = Path(preset_html_path).read_text(encoding="utf-8")
    # Extract template literal assigned to csvData: `...`
    match = re.search(r"csvData:\s*`(?P<data>.*?)`", html, flags=re.DOTALL)
    if not match:
        raise ValueError(
            "No --csv path provided and no embedded csvData template literal found in preset HTML."
        )

    data = match.group("data")
    # Undo safe escaping used by _embed_csv_in_preset.py
    data = data.replace("\\`", "`").replace("\\${", "${")
    return data


def infer_columns(headers: list[str]) -> tuple[int, int]:
    lowered = [h.strip().lower() for h in headers]
    ts_candidates = [
        i
        for i, h in enumerate(lowered)
        if "time" in h or "timestamp" in h or "date" in h
    ]
    glucose_candidates_primary = [
        i
        for i, h in enumerate(lowered)
        if "measurement" in h or "mg/dl" in h or "value" in h
    ]
    glucose_candidates_secondary = [
        i
        for i, h in enumerate(lowered)
        if "glucose" in h and i not in ts_candidates
    ]

    ts_idx = ts_candidates[0] if ts_candidates else 0
    if glucose_candidates_primary:
        glucose_idx = glucose_candidates_primary[0]
    elif glucose_candidates_secondary:
        glucose_idx = glucose_candidates_secondary[0]
    else:
        glucose_idx = 1 if len(headers) > 1 else 0

    if glucose_idx == ts_idx and len(headers) > 1:
        glucose_idx = 1 if ts_idx == 0 else 0

    return ts_idx, glucose_idx


def parse_cgm_rows(csv_text: str) -> list[CgmPoint]:
    text = csv_text.strip()
    stream = io.StringIO(text)
    sample = stream.read(4096)
    stream.seek(0)

    def score_delimiter(delim: str) -> int:
        lines = text.splitlines()[:250]
        if len(lines) <= 1:
            return 0
        body = lines[1:]
        return sum(1 for line in body if delim in line)

    # Prefer delimiter that appears consistently in body lines.
    delim_scores = {
        ",": score_delimiter(","),
        "\t": score_delimiter("\t"),
        ";": score_delimiter(";"),
    }
    best_delim = max(delim_scores, key=delim_scores.get)

    if delim_scores[best_delim] > 0:
        reader = csv.reader(stream, delimiter=best_delim)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    else:
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        except csv.Error:
            dialect = csv.get_dialect("excel")
        reader = csv.reader(stream, dialect)
        rows = [row for row in reader if any(cell.strip() for cell in row)]

    # Safety fallback for malformed detection cases where each row stayed unsplit.
    if rows and len(rows) > 1 and all(len(r) == 1 for r in rows[1:50]):
        if "\t" in rows[1][0]:
            rows = [r[0].split("\t") for r in rows]
        elif "," in rows[1][0]:
            rows = [r[0].split(",") for r in rows]

    if not rows:
        raise ValueError("CSV appears empty.")

    header = rows[0]
    if len(header) == 1 and len(rows) > 1 and len(rows[1]) > 1:
        # Some Lingo exports use a comma-containing single-cell header line,
        # while data rows are tab-delimited across multiple columns.
        header = ["timestamp", "glucose"] + [f"col{i}" for i in range(2, len(rows[1]))]

    ts_idx, glucose_idx = infer_columns(header)

    # Detect whether first row is header by testing timestamp parse.
    start_idx = 0
    try:
        _ = parse_timestamp(rows[0][ts_idx].strip())
    except Exception:
        start_idx = 1

    points: list[CgmPoint] = []
    for row in rows[start_idx:]:
        if len(row) <= max(ts_idx, glucose_idx):
            continue

        ts_raw = row[ts_idx].strip()
        g_raw = row[glucose_idx].strip()
        if not ts_raw or not g_raw:
            continue

        try:
            ts = parse_timestamp(ts_raw)
            glucose = float(g_raw)
        except Exception:
            continue

        points.append(CgmPoint(ts=ts, glucose=glucose))

    if not points:
        raise ValueError("No valid CGM points parsed from CSV.")

    points.sort(key=lambda p: p.ts)
    return points


def filter_day(points: list[CgmPoint], target_date: datetime.date) -> list[CgmPoint]:
    day_points = [p for p in points if p.ts.date() == target_date]
    if not day_points:
        raise ValueError(f"No CGM points found for date {target_date.isoformat()}.")
    return day_points


def detect_spike(points: list[CgmPoint], threshold: float) -> SpikeEvent | None:
    if not points:
        return None

    in_spike = False
    onset = None
    segment_points: list[CgmPoint] = []
    segments: list[list[CgmPoint]] = []

    for p in points:
        if p.glucose > threshold:
            if not in_spike:
                in_spike = True
                onset = p.ts
                segment_points = []
            segment_points.append(p)
        else:
            if in_spike and segment_points:
                segments.append(segment_points)
            in_spike = False
            onset = None
            segment_points = []

    if in_spike and segment_points:
        segments.append(segment_points)

    if not segments:
        return None

    # Pick the segment with the highest peak; tiebreak by earlier onset.
    segments.sort(key=lambda seg: (-max(p.glucose for p in seg), seg[0].ts))
    best = segments[0]
    peak_point = max(best, key=lambda p: p.glucose)

    # Estimate duration from first to last point in the segment.
    duration = int((best[-1].ts - best[0].ts).total_seconds() // 60)

    return SpikeEvent(
        onset=best[0].ts,
        peak_time=peak_point.ts,
        peak_value=peak_point.glucose,
        duration_minutes=max(duration, 0),
    )


def minutes_since_midnight(ts: datetime) -> float:
    return ts.hour * 60 + ts.minute + ts.second / 60.0


def compute_sampling_minutes(points: list[CgmPoint]) -> int:
    if len(points) < 2:
        return 5
    deltas = [
        int((points[i].ts - points[i - 1].ts).total_seconds() // 60)
        for i in range(1, len(points))
    ]
    deltas = [d for d in deltas if d > 0]
    if not deltas:
        return 5
    return int(median(deltas))


def format_spike_note(spike: SpikeEvent) -> list[str]:
    return [
        (
            f"[GLYCEMIC SPIKE] Elevated excursion detected starting at "
            f"{spike.onset.strftime('%H:%M')}."
        ),
        (
            f"Reached a peak amplitude of {spike.peak_value:.0f} mg/dL at "
            f"{spike.peak_time.strftime('%H:%M')} "
            f"(Total duration: {spike.duration_minutes} minutes)."
        ),
    ]


def plot_report(
    day_points: list[CgmPoint],
    target_date: datetime.date,
    output_path: Path,
    target_low: float,
    target_high: float,
    note_lines: list[str],
) -> None:
    xs = [minutes_since_midnight(p.ts) / 60.0 for p in day_points]
    ys = [p.glucose for p in day_points]

    in_range_mask = [target_low <= y <= target_high for y in ys]
    high_mask = [y > target_high for y in ys]

    mean_glucose = sum(ys) / len(ys)
    min_glucose = min(ys)
    max_glucose = max(ys)
    tir = 100.0 * sum(in_range_mask) / len(ys)
    below = 100.0 * sum(y < target_low for y in ys) / len(ys)
    above = 100.0 * sum(high_mask) / len(ys)

    fig, ax = plt.subplots(figsize=(12.8, 9.6), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Reserve lower area for the summary and notes box.
    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.39)

    ax.axhspan(target_low, target_high, color="#dcead9", alpha=0.65, zorder=0)
    ax.axhline(target_low, color="#66bb6a", linestyle=(0, (4, 2)), linewidth=1.0)
    ax.axhline(target_high, color="#ef6c00", linestyle=(0, (4, 2)), linewidth=1.0)

    ax.plot(xs, ys, color="#c4c4c4", linewidth=1.8, alpha=0.9, zorder=1)

    in_x = [x for x, keep in zip(xs, in_range_mask) if keep]
    in_y = [y for y, keep in zip(ys, in_range_mask) if keep]
    hi_x = [x for x, keep in zip(xs, high_mask) if keep]
    hi_y = [y for y, keep in zip(ys, high_mask) if keep]

    ax.scatter(in_x, in_y, s=14, color="#3f914a", alpha=0.8, zorder=2)
    if hi_x:
        ax.scatter(hi_x, hi_y, s=22, color="#ff7f0e", alpha=0.95, zorder=3)

    title_date = target_date.strftime("%A, %B %d, %Y")
    ax.set_title(
        f"Continuous Glucose Monitoring Profile - {title_date}",
        fontsize=18,
        fontweight="bold",
        pad=14,
    )
    ax.set_ylabel("Glucose Level (mg/dL)", fontsize=16, fontweight="bold")

    ax.set_xlim(0, 24)
    ax.set_ylim(40, 180)
    ax.set_xticks(list(range(0, 25, 3)))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 25, 3)], fontsize=13)
    ax.set_yticks(list(range(40, 181, 20)))
    ax.tick_params(axis="y", labelsize=15)
    ax.grid(True, linestyle=(0, (1, 2)), linewidth=0.9, color="#c9c9c9", alpha=0.85)

    legend_handles = [
        Patch(facecolor="#dcead9", edgecolor="#dcead9", alpha=0.65, label=f"Target Range ({int(target_low)}-{int(target_high)} mg/dL)"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=5, markerfacecolor="#3f914a", markeredgecolor="#3f914a", alpha=0.9, label="In Target"),
        Line2D([0], [0], marker="o", linestyle="None", markersize=6, markerfacecolor="#ff7f0e", markeredgecolor="#ff7f0e", alpha=0.95, label=f"High (>{int(target_high)} mg/dL)"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=True, framealpha=0.95, fontsize=12)

    summary_line_1 = (
        f"• Mean Glucose: {mean_glucose:.1f} mg/dL    "
        f"• Min: {min_glucose:.0f} mg/dL    "
        f"• Max: {max_glucose:.0f} mg/dL"
    )
    summary_line_2 = (
        f"• Time-In-Range ({int(target_low)}-{int(target_high)} mg/dL): {tir:.1f}%    "
        f"• Below {int(target_low)}: {below:.1f}%    "
        f"• Above {int(target_high)}: {above:.1f}%"
    )

    note_text = "\n".join(textwrap.fill(line, width=95) for line in note_lines) if note_lines else "• No clinical notes provided."

    full_text = (
        "DAILY METRICS SUMMARY:\n"
        f"{summary_line_1}\n"
        f"{summary_line_2}\n\n"
        "CLINICAL DIARY LOGS & NOTES:\n"
        f"• {note_text}"
    )

    fig.text(
        0.09,
        0.08,
        full_text,
        ha="left",
        va="bottom",
        fontsize=14,
        linespacing=1.35,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#fafafa", edgecolor="#d0d0d0", alpha=0.95),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def main() -> int:
    args = parse_args()

    try:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    except ValueError:
        print("Error: --date must be in YYYY-MM-DD format.", file=sys.stderr)
        return 2

    if args.target_low >= args.target_high:
        print("Error: --target-low must be less than --target-high.", file=sys.stderr)
        return 2

    try:
        csv_text = load_csv_text(args.csv, args.preset_html)
        points = parse_cgm_rows(csv_text)
        day_points = filter_day(points, target_date)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    notes = list(args.note)
    if not args.no_auto_spike_note:
        spike = detect_spike(day_points, args.target_high)
        if spike:
            notes.extend(format_spike_note(spike))

    if not notes:
        notes = ["No glycemic spike above target range detected for this date."]

    output = Path(args.output) if args.output else Path(f"cgm_report_{target_date.isoformat()}.png")

    try:
        plot_report(
            day_points=day_points,
            target_date=target_date,
            output_path=output,
            target_low=args.target_low,
            target_high=args.target_high,
            note_lines=notes,
        )
    except Exception as exc:
        print(f"Error: failed to generate plot: {exc}", file=sys.stderr)
        return 1

    print(f"Saved report: {output}")
    print(f"Data points used: {len(day_points)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
