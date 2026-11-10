"""Convert LINZ Auckland standard-port tide CSVs into a compact list of high/low events.

    python scripts/build_tides.py            -> data/tides.json

Input: data/linz/Auckland YYYY.csv, downloaded from
https://static.charts.linz.govt.nz/tide-tables/maj-ports/csv/Auckland%20YYYY.csv
Each row is one day: day, weekday, month, year, then up to four (time, height) pairs in
NZ local time (standard or daylight, whichever was in force). Heights are metres above
chart datum.

Output: [[epoch_seconds_utc, height_m, "H"|"L"], ...] sorted by time. Add next year's CSV
to data/linz/ each year (LINZ usually publishes two or three years ahead).
"""
import csv
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
NZ = ZoneInfo("Pacific/Auckland")


def read_csv(path):
    events = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if len(row) < 6 or not row[0].strip().isdigit() or not row[3].strip().isdigit():
                continue  # header lines
            day, month, year = int(row[0]), int(row[2]), int(row[3])
            pairs = row[4:]
            for i in range(0, len(pairs) - 1, 2):
                t, h = pairs[i].strip(), pairs[i + 1].strip()
                if not t or not h:
                    continue
                hh, mm = map(int, t.split(":"))
                # fold=0: during the one ambiguous hour at the end of daylight saving, take the
                # first occurrence. LINZ prints local time, so this is at most a 1-hour edge case.
                local = datetime(year, month, day, hh, mm, tzinfo=NZ)
                events.append([int(local.timestamp()), float(h)])
    return events


def main():
    events = []
    for path in sorted((ROOT / "data" / "linz").glob("Auckland *.csv")):
        events += read_csv(path)
    events.sort()
    # Dedupe (year files can overlap at the boundary) and label highs/lows by comparing
    # with neighbours: tides alternate, so each event is higher or lower than both sides.
    out = []
    for e in events:
        if out and out[-1][0] == e[0]:
            continue
        out.append(e)
    for i, e in enumerate(out):
        nb = [out[j][1] for j in (i - 1, i + 1) if 0 <= j < len(out)]
        e.append("H" if e[1] > max(nb) else "L")
    bad = [i for i in range(1, len(out)) if out[i][2] == out[i - 1][2]]
    if bad:
        raise SystemExit(f"non-alternating highs/lows at {len(bad)} places, first {out[bad[0]]}")
    dst = ROOT / "data" / "tides.json"
    dst.write_text(json.dumps(out, separators=(",", ":")))
    first = datetime.fromtimestamp(out[0][0], NZ)
    last = datetime.fromtimestamp(out[-1][0], NZ)
    print(f"{dst}: {len(out)} events, {first:%Y-%m-%d} to {last:%Y-%m-%d}")


if __name__ == "__main__":
    main()
