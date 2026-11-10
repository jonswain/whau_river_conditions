"""Inject tide events into src/template.html.

    python scripts/build.py                   -> build/index.html (local preview)
    python scripts/build.py --standalone OUT  -> OUT, a blog-ready page, e.g.
        ../jonswain.github.io/visualisations/whau-conditions/index.html

Tides are fixed predictions, so they're baked in. Weather and rain come from Open-Meteo in the
browser.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from standalone import wrap  # noqa: E402

SLUG = "whau-conditions"
DESCRIPTION = ("Tide, Whau Stream flow, wind and light for rowing on the Whau River in Auckland, "
               "now or at any time up to two weeks ahead.")
IMAGE = f"/images/visualisations/{SLUG}.png"


def build():
    html = (ROOT / "src" / "template.html").read_text()
    assert "/*DATA*/null" in html
    data = {"tides": json.loads((ROOT / "data" / "tides.json").read_text())}
    blob = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    return html.replace("/*DATA*/null", blob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--standalone", type=Path, help="write a blog-ready page to this path")
    args = ap.parse_args()
    out = args.standalone or ROOT / "build" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(wrap(build(), SLUG, DESCRIPTION, IMAGE))
    print(out, out.stat().st_size)


if __name__ == "__main__":
    main()
