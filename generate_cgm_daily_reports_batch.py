#!/usr/bin/env python3
"""Batch-generate styled daily CGM PNG reports for a date range."""

from __future__ import annotations

import argparse
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
        description="Generate daily CGM reports for each day in an inclusive date range."
    )
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD).")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD).")
    parser.add_argument("--csv", help="Path to source CSV. Optional if preset HTML has embedded csvData.")
    parser.add_argument(
        "--preset-html",
        default="cgm-tracker.html",
        help="HTML file containing embedded PRESET_CYCLE csvData template literal.",
    )
    parser.add_argument(
        "--output-dir",
        default="cgm-graphics/2026-cycle-1",
        help="Folder where report PNG files will be written.",
    )
    parser.add_argument(
        "--filename-template",
        default="cgm_report_{date}.png",
        help="Output filename pattern. Use {date} token for YYYY-MM-DD.",
    )
    parser.add_argument("--target-low", type=float, default=70.0, help="Lower target range threshold.")
    parser.add_argument("--target-high", type=float, default=140.0, help="Upper target range threshold.")
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="Static note line to include in each report. Can be used multiple times.",
    )
    parser.add_argument(
        "--no-auto-spike-note",
        action="store_true",
        help="Disable automatic glycemic spike note generation.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing PNG files if they already exist.",
    )
    return parser.parse_args()


def date_range(start: datetime.date, end: datetime.date):
    current = start
    while current <= end:
        yield current
        current = current + timedelta(days=1)


def main() -> int:
    args = parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    end = datetime.strptime(args.end_date, "%Y-%m-%d").date()

    if end < start:
        raise ValueError("--end-date must be on or after --start-date.")

    if args.target_low >= args.target_high:
        raise ValueError("--target-low must be less than --target-high.")

    csv_text = load_csv_text(args.csv, args.preset_html)
    points = parse_cgm_rows(csv_text)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0
    missing = 0

    for day in date_range(start, end):
        try:
            day_points = filter_day(points, day)
        except ValueError:
            missing += 1
            print(f"[missing] {day.isoformat()} (no data)")
            continue

        filename = args.filename_template.format(date=day.isoformat())
        output_path = output_dir / filename

        if output_path.exists() and not args.overwrite:
            skipped += 1
            print(f"[skip] {output_path} already exists")
            continue

        notes = list(args.note)
        if not args.no_auto_spike_note:
            spike = detect_spike(day_points, args.target_high)
            if spike:
                notes.extend(format_spike_note(spike))
        if not notes:
            notes = ["No glycemic spike above target range detected for this date."]

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

    print(
        f"Done. generated={generated} skipped={skipped} missing={missing} "
        f"range={start.isoformat()}..{end.isoformat()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
