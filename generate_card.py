#!/usr/bin/env python3
"""Fetch POTA stats for a callsign and write an SVG stats card.

Uses only the Python standard library. If the fetch fails, the script exits
with an error and leaves the previous card untouched.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

CALLSIGN = "KF5WZD"
API_URL = f"https://api.pota.app/stats/user/{CALLSIGN}"
OUT_FILE = Path("docs/pota-stats.svg")

# Colors match the QRZ page
BG, BORDER = "#16181b", "#5a5f66"
ACCENT, TEXT, MUTED = "#7fd4e0", "#f0f0f0", "#aab0b8"


def fetch_stats():
    req = urllib.request.Request(
        API_URL, headers={"User-Agent": f"{CALLSIGN}-qrz-stats-card"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def get(data, *keys):
    """Safely read a nested number; returns 0 if anything is missing."""
    for key in keys:
        if not isinstance(data, dict):
            return 0
        data = data.get(key, 0)
    return data if isinstance(data, (int, float)) else 0


def stat(x, y, value, label):
    return (
        f'<text x="{x}" y="{y}" text-anchor="middle" font-size="44" '
        f'font-weight="bold" fill="{TEXT}">{value:,}</text>'
        f'<text x="{x}" y="{y + 24}" text-anchor="middle" font-size="13" '
        f'letter-spacing="1.5" fill="{ACCENT}">{escape(label.upper())}</text>'
    )


def build_svg(data):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xs = (160, 400, 640)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 340" '
        'width="800" height="340" role="img" '
        f'aria-label="{escape(CALLSIGN)} POTA statistics" '
        'font-family="Arial, Helvetica, sans-serif">',
        f"<title>{escape(CALLSIGN)} POTA statistics</title>",
        f'<rect x="1" y="1" width="798" height="338" rx="17" fill="{BG}" '
        f'stroke="{BORDER}" stroke-width="1"/>',
        f'<text x="400" y="50" text-anchor="middle" font-size="26" '
        f'font-weight="bold" fill="{ACCENT}">POTA Stats &#183; {escape(CALLSIGN)}</text>',
        f'<line x1="40" y1="68" x2="760" y2="68" stroke="{BORDER}"/>',
        f'<text x="40" y="98" font-size="14" letter-spacing="2" fill="{MUTED}">ACTIVATOR</text>',
        stat(xs[0], 146, get(data, "activator", "activations"), "Activations"),
        stat(xs[1], 146, get(data, "activator", "parks"), "Parks"),
        stat(xs[2], 146, get(data, "activator", "qsos"), "QSOs"),
        f'<text x="40" y="206" font-size="14" letter-spacing="2" fill="{MUTED}">HUNTER &amp; AWARDS</text>',
        stat(xs[0], 254, get(data, "hunter", "parks"), "Parks Hunted"),
        stat(xs[1], 254, get(data, "hunter", "qsos"), "Hunter QSOs"),
        stat(xs[2], 254, get(data, "awards"), "Awards"),
        f'<text x="400" y="322" text-anchor="middle" font-size="12" fill="{MUTED}">'
        f"Updated {today} UTC &#183; Data from pota.app</text>",
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    try:
        data = fetch_stats()
        if "activator" not in data:
            raise ValueError("Unexpected response: no 'activator' section")
    except Exception as exc:  # leave the old card in place on any failure
        print(f"Could not update stats: {exc}", file=sys.stderr)
        sys.exit(1)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(build_svg(data), encoding="utf-8")
    print(f"Wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
