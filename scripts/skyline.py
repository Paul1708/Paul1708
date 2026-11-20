#!/usr/bin/env python3
"""Rebuild the skyline in assets/night-train.svg from my GitHub contributions.

Between Erfurt and Jena, every week of the last year with contributions adds
a tower to the city. Each active day is one floor with a lit window; the
brighter the window, the busier the day. The current week is still under
construction.
"""

import datetime as dt
import os
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

USER = os.environ.get("SKYLINE_USER", "Paul1708")
SVG = Path(__file__).resolve().parent.parent / "assets" / "night-train.svg"

WEEKS = 53
LEFT = 140  # x of the first building
WIDTH = 8  # one slot per week
BASE = 108  # top edge of the track bed; towers stand behind it
FLOOR = 5

START, END = "<!-- skyline:start -->", "<!-- skyline:end -->"


def fetch_days() -> dict[dt.date, int]:
    url = f"https://github.com/users/{USER}/contributions"
    request = urllib.request.Request(url, headers={"User-Agent": "skyline"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode()

    days = {}
    for tag in re.findall(r"<td\b[^>]*\bdata-date=[^>]*>", html):
        date = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        level = re.search(r'data-level="([0-4])"', tag)
        if date and level:
            days[dt.date.fromisoformat(date.group(1))] = int(level.group(1))

    if len(days) < 365:
        raise RuntimeError(f"Expected a full year of contributions, found {len(days)} days.")
    return days


def group_by_week(days: dict[dt.date, int]) -> list[list[int]]:
    weeks = defaultdict(list)
    for date in sorted(days):
        sunday = date - dt.timedelta(days=(date.weekday() + 1) % 7)
        weeks[sunday].append(days[date])
    return [weeks[sunday] for sunday in sorted(weeks)][-WEEKS:]


def render(weeks: list[list[int]]) -> str:
    towers, antennas = [], []
    windows = defaultdict(list)

    for index, levels in enumerate(weeks):
        busy = [level for level in levels if level]
        if not busy:
            continue
        x = LEFT + index * WIDTH
        top = BASE - 14 - FLOOR * len(busy)
        towers.append(f"M{x + 1} {top}h6v{BASE + 2 - top}h-6z")
        if len(busy) >= 5:
            antennas.append(f"M{x + 3} {top - 5}h2v5h-2z")
        for floor, level in enumerate(busy):
            windows[level].append(f"M{x + 3} {BASE - 9 - FLOOR * floor}h2v2h-2z")

    # The current week is still being built.
    x = LEFT + (len(weeks) - 1) * WIDTH
    jib = BASE - 48
    crane = (
        f"M{x + WIDTH + 2} {BASE}V{jib}h2V{BASE}z"
        f"M{x - 4} {jib - 2}h24v2h-24z"
        f"M{x + 4} {jib}h1v7h-1z"
        f"M{x + 3} {jib + 7}h3v2h-3z"
    )

    lines = [
        START,
        f'<path class="crane" d="{crane}"/>',
        f'<path class="tower" d="{"".join(towers + antennas)}"/>',
    ]
    lines += [f'<path class="lit l{level}" d="{"".join(windows[level])}"/>' for level in sorted(windows)]
    lines.append(END)
    return "\n    ".join(lines)


def main() -> int:
    svg = SVG.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + ".*?" + re.escape(END), re.S)
    if not pattern.search(svg):
        print(f"No skyline markers in {SVG}", file=sys.stderr)
        return 1

    skyline = render(group_by_week(fetch_days()))
    updated = pattern.sub(lambda _: skyline, svg)
    if updated != svg:
        SVG.write_text(updated, encoding="utf-8", newline="\n")
        print("Skyline rebuilt.")
    else:
        print("Skyline unchanged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
