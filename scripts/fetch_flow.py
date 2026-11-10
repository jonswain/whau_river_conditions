"""Fetch Whau Stream flow from LAWA and write docs/flow.json for the page.

    python scripts/fetch_flow.py              -> docs/flow.json (last 7 days, 15-min)
    python scripts/fetch_flow.py --baseline   -> also refresh data/flow_baseline.json (1 year)

Source: LAWA's site page for the Auckland Council "Whau" flow gauge,
https://www.lawa.org.nz/explore-data/auckland-region/water-quantity/monitoring-sites/whau-flow
which charts data from /umbraco/api/sensorservice/GetLineChartSeriesDataForProperty.
That endpoint sends no CORS header, so the page can't call it directly; a GitHub Action runs
this script and publishes the result with GitHub Pages instead.

Quirk: LAWA's timestamps are NZ local wall-clock time encoded as if it were UTC (the Flot
chart convention), so they are re-interpreted as Pacific/Auckland here.

Fails soft: if LAWA is down, the previous flow.json is left in place with an "error" field,
so the page can still show the last good reading and say how old it is.
"""
import argparse
import json
import statistics
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
NZ = ZoneInfo("Pacific/Auckland")
PAGE_ID = "50416"  # LAWA page id for the Whau flow site
API = "https://www.lawa.org.nz/umbraco/api/sensorservice/GetLineChartSeriesDataForProperty"
SITE_URL = ("https://www.lawa.org.nz/explore-data/auckland-region/water-quantity/"
            "monitoring-sites/whau-flow")
OUT = ROOT / "docs" / "flow.json"
BASELINE = ROOT / "data" / "flow_baseline.json"
STEP = 15 * 60  # resample the ~2-min record to 15 min to keep the file small


def fetch(duration, timeout=120):
    q = urllib.parse.urlencode({"pageId": PAGE_ID, "property": "dischargeContinuous",
                                "duration": duration, "expectedUnits": "m3/s"})
    req = urllib.request.Request(f"{API}?{q}", headers={"User-Agent": "whau-river-conditions/1.0",
                                                        "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    if d.get("Error") or not d.get("Series"):
        raise RuntimeError(f"LAWA returned no series: {d.get('Error')!r}")
    pts = []
    for ms, v in d["Series"][0]["data"]:
        if v is None:
            continue
        wall = datetime.fromtimestamp(ms / 1000, timezone.utc).replace(tzinfo=NZ)
        pts.append((int(wall.timestamp()), float(v)))
    pts.sort()
    if not pts:
        raise RuntimeError("LAWA series is empty")
    return pts


def resample(pts, step=STEP):
    """Mean of each step-long bucket, but keep the bucket max too so flood peaks survive."""
    buckets = {}
    for t, v in pts:
        buckets.setdefault(t - t % step, []).append(v)
    return [[t, round(statistics.fmean(vs), 4), round(max(vs), 4)]
            for t, vs in sorted(buckets.items())]


def baseline():
    pts = fetch("P1Y", timeout=300)
    vals = sorted(v for _, v in pts)
    pct = lambda p: round(vals[min(len(vals) - 1, int(p / 100 * len(vals)))], 4)  # noqa: E731
    out = {
        "computed": datetime.now(NZ).isoformat(timespec="minutes"),
        "from": datetime.fromtimestamp(pts[0][0], NZ).isoformat(timespec="minutes"),
        "to": datetime.fromtimestamp(pts[-1][0], NZ).isoformat(timespec="minutes"),
        "n": len(vals),
        "percentiles": {str(p): pct(p) for p in (10, 25, 50, 75, 90, 95, 99)},
        "max": vals[-1],
    }
    BASELINE.write_text(json.dumps(out, indent=2) + "\n")
    print(f"{BASELINE}: median {out['percentiles']['50']} m3/s, p95 {out['percentiles']['95']}, "
          f"max {out['max']} over {out['from']} to {out['to']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true", help="also recompute the 1-year baseline")
    args = ap.parse_args()
    if args.baseline:
        baseline()
    base = json.loads(BASELINE.read_text()) if BASELINE.exists() else None
    now = datetime.now(NZ).isoformat(timespec="seconds")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        pts = fetch("P7D")
    except Exception as e:  # noqa: BLE001 - fail soft, keep the last good data
        prev = json.loads(OUT.read_text()) if OUT.exists() else {}
        prev.update({"checked": now, "error": f"{type(e).__name__}: {e}"})
        OUT.write_text(json.dumps(prev, separators=(",", ":")))
        print(f"LAWA fetch failed, kept previous data: {e}", file=sys.stderr)
        return
    series = resample(pts)
    latest_t, latest_v = pts[-1]
    out = {
        "site": "Whau Stream (Auckland Council gauge via LAWA)",
        "source": SITE_URL,
        "units": "m3/s",
        "checked": now,
        "latest": {"t": latest_t, "v": latest_v},
        "baseline": base,
        "series": series,  # [epoch_s, mean, max] per 15 min, oldest first
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"{OUT}: {len(series)} points, latest {latest_v} m3/s at "
          f"{datetime.fromtimestamp(latest_t, NZ):%Y-%m-%d %H:%M}")


if __name__ == "__main__":
    main()
