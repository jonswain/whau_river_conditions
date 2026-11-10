# Whau River Conditions

One page for rowing on the Whau River from West End Rowing Club: tide, Whau Stream (from rain),
wind and light, now or at any time up to about two weeks ahead. It's published on the blog at
`/visualisations/whau-conditions/`.

| Source | What it gives | How it's loaded |
|---|---|---|
| LINZ Auckland standard-port tide tables | High and low water times and heights | Built into the page (`data/tides.json`) |
| Open-Meteo | Hourly wind, gusts, rain (past 8 days and forecast), temperature | Fetched by the browser |
| Calculated here | First light, sunrise, sunset, last light | In the page |

## Layout

```
data/linz/Auckland YYYY.csv   LINZ tide CSVs (add next year's each year)
data/tides.json               built by scripts/build_tides.py
src/template.html             the page
scripts/build.py              template + data → standalone page
scripts/standalone.py         blog wrapper (same as the rowing projects)
```

## Commands

```bash
python scripts/build_tides.py            # after adding a new LINZ CSV
python scripts/build.py                  # build/index.html for local preview
python scripts/build.py --standalone ../jonswain.github.io/visualisations/whau-conditions/index.html
```

Only the Python standard library is needed (3.9+).

## Tuning

- **Settings panel on the page** (saved per browser): the tide time offset from Auckland.
- **`CFG` at the top of the script in `src/template.html`:** the default offset, the S-bend rule
  (`sBendHours`, above the S-bend only within 2 h of high water), the wind and gust thresholds
  (km/h), and the river's downstream bearing.
- **`CFG.harbour`:** the harbour badge. Wind speed is scaled by how exposed each direction is
  (N–E has a long fetch, ×1.3; SE–WNW is over land, ×0.7), then graded: good below 8 km/h with
  gusts below 18 km/h, marginal below 14/28 km/h. Wind against the harbour's tide drops it a
  grade. `ebbTo` is the rough direction the ebb runs at the Whau mouth.
- **`CFG.windTide`:** the Whau wind-against-tide badge. It counts when the wind is at least
  10 km/h, the tide is changing at least 0.2 m/h, and the wind is within ±50° of directly
  opposing the current.

## Notes

- **Stream from rain.** `CFG.stream` calls the stream "Up" at 6 mm and "High" at 15 mm of rain in the
  6 h before the chosen time. These were calibrated in Nov 2026 against a year of the Auckland
  Council Whau gauge (Whau Stream @ Blockhouse Bay Road, via LAWA) and Open-Meteo hourly rain:
  - At 6 mm or more, flow was in its top 5% about 70% of the time, catching about 60% of those hours.
  - At 15 mm or more, it was in its top 1% about 40% of the time.
  - 24 h and 48 h totals were worse predictors; the stream is usually back to normal within about
    6 h of rain stopping.

  An earlier version read the gauge directly, but LAWA blocks requests from GitHub Actions,
  so it was dropped (see git history).
- LINZ tide CSVs: `https://static.charts.linz.govt.nz/tide-tables/maj-ports/csv/Auckland%20YYYY.csv`.
  The current data runs to the end of 2027, and the page says so when a date has no predictions.
