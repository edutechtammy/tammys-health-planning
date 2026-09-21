#!/usr/bin/env python3
"""Create a full CGM cycle folder with daily reports and updated manifests."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from generate_cgm_daily_report import (
    detect_spike,
    filter_day,
    format_spike_note,
    load_csv_text,
    parse_cgm_rows,
    plot_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a complete cycle folder of daily CGM reports and update "
            "cgm-graphics manifests in one command."
        )
    )
    parser.add_argument("--cycle", required=True, help="Cycle folder name, for example 2026-cycle-3")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--csv", help="Path to source CSV. Optional if preset HTML has embedded csvData.")
    parser.add_argument(
        "--preset-html",
        default="cgm-tracker.html",
        help="HTML file containing embedded PRESET_CYCLE csvData template literal.",
    )
    parser.add_argument("--target-low", type=float, default=70.0, help="Lower target threshold")
    parser.add_argument("--target-high", type=float, default=140.0, help="Upper target threshold")
    parser.add_argument(
        "--graphics-root",
        default="cgm-graphics",
        help="Root graphics folder containing cycle subfolders and root index.json",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Static note line(s) to include in each report.",
    )
    parser.add_argument(
        "--no-auto-spike-note",
        action="store_true",
        help="Disable auto-generated glycemic spike notes.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing report files.",
    )
    return parser.parse_args()


def iter_days(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def month_day_year(dt):
    return f"{dt.strftime('%B')} {dt.day}, {dt.year}"


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def update_root_manifest(root_manifest_path: Path, cycle_name: str) -> None:
    root_manifest = read_json(root_manifest_path, [])
    if not isinstance(root_manifest, list):
        raise ValueError(f"Root manifest is not a JSON list: {root_manifest_path}")

    if cycle_name not in root_manifest:
        root_manifest.append(cycle_name)

    def cycle_sort_key(name: str):
        m = re.match(r"^(\d{4})-cycle-(\d+)$", name)
        if m:
            return (1, int(m.group(1)), int(m.group(2)))
        if name == "0-Overview":
            return (0, 0, 0)
        return (2, name)

    root_manifest = sorted(root_manifest, key=cycle_sort_key)
    root_manifest_path.write_text(json.dumps(root_manifest, indent=2) + "\n", encoding="utf-8")


def merge_cycle_manifest(cycle_dir: Path, new_daily_entries: list[dict]) -> list[dict]:
    cycle_manifest_path = cycle_dir / "index.json"
    existing_manifest = read_json(cycle_manifest_path, [])
    existing_by_file = {}
    if isinstance(existing_manifest, list):
        for item in existing_manifest:
            if isinstance(item, dict) and "file" in item:
                existing_by_file[item["file"]] = item

    new_daily_files = {entry["file"] for entry in new_daily_entries}

    merged = []

    # Keep all existing non-daily entries first.
    for filename, item in existing_by_file.items():
        if filename not in new_daily_files:
            merged.append(item)

    # Ensure non-daily PNG files in folder are represented (even if they were never indexed).
    indexed_files = {item.get("file") for item in merged if isinstance(item, dict)}
    for png_path in sorted(cycle_dir.glob("*.png")):
        fname = png_path.name
        if fname.startswith("cgm_report_"):
            continue
        if fname not in indexed_files:
            merged.append(
                {
                    "file": fname,
                    "caption": f"CGM cycle asset: {png_path.stem.replace('_', ' ')}.",
                }
            )

    # Append new daily entries, ordered by date filename.
    merged.extend(sorted(new_daily_entries, key=lambda x: x["file"]))
    return merged


def main() -> int:
    args = parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    if end < start:
        raise ValueError("--end-date must be on or after --start-date")
    if args.target_low >= args.target_high:
        raise ValueError("--target-low must be lower than --target-high")

    graphics_root = Path(args.graphics_root)
    cycle_dir = graphics_root / args.cycle
    cycle_dir.mkdir(parents=True, exist_ok=True)

    csv_text = load_csv_text(args.csv, args.preset_html)
    points = parse_cgm_rows(csv_text)

    generated = 0
    skipped = 0
    missing = 0
    manifest_entries = []

    for day in iter_days(start, end):
        filename = f"cgm_report_{day.isoformat()}.png"
        output_path = cycle_dir / filename

        try:
            day_points = filter_day(points, day)
        except ValueError:
            missing += 1
            print(f"[missing] {day.isoformat()} (no data)")
            continue

        notes = list(args.note)
        if not args.no_auto_spike_note:
            spike = detect_spike(day_points, args.target_high)
            if spike:
                notes.extend(format_spike_note(spike))
        if not notes:
            notes = ["No glycemic spike above target range detected for this date."]

        if output_path.exists() and not args.overwrite:
            skipped += 1
            print(f"[skip] {output_path} already exists")
        else:
            plot_report(
                day_points=day_points,
                target_date=day,
                output_path=output_path,
                target_low=args.target_low,
                target_high=args.target_high,
                note_lines=notes,
            )
            generated += 1
            print(f"[ok] {output_path}")

        manifest_entries.append(
            {
                "file": filename,
                "caption": f"Daily CGM report for {month_day_year(day)}.",
            }
        )

    cycle_manifest_path = cycle_dir / "index.json"
    merged_manifest = merge_cycle_manifest(cycle_dir, manifest_entries)
    cycle_manifest_path.write_text(
        json.dumps(merged_manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    root_manifest_path = graphics_root / "index.json"
    update_root_manifest(root_manifest_path, args.cycle)

    print(
        f"Done. generated={generated} skipped={skipped} missing={missing} "
        f"cycle={args.cycle} range={start.isoformat()}..{end.isoformat()}"
    )
    print(f"Updated: {cycle_manifest_path}")
    print(f"Updated: {root_manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
