"""
render_heatmap_svg.py — draw the classic 53-week x 7-day contribution grid
as rounded, colored boxes that slide in diagonally, line after line, once
(no looping). Adds a Less->More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py

Output:
    contrib-heatmap.svg
"""

import json
from datetime import date

# none -> brightest (an extra neon top tier beyond GitHub's usual 5)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
LEFT_MARGIN = 30
TOP_MARGIN = 20
FOOTER_HEIGHT = 40
LEGEND_HEIGHT = 26

WEEKS = 53
DAYS = 7

STAGGER_PER_WEEK = 0.03
CELL_DUR = 0.35


def load_data(path: str = "data/contributions.json") -> dict:
    with open(path) as f:
        return json.load(f)


def bucket_into_weeks(days: list[dict]) -> list[list[dict | None]]:
    """
    Arrange day records into WEEKS columns x DAYS rows, aligned so each
    column is a Sun-Sat week, matching GitHub's own layout.
    """
    weeks: list[list[dict | None]] = []
    current_week: list[dict | None] = [None] * DAYS

    for d in days:
        y, m, day_num = (int(x) for x in d["date"].split("-"))
        weekday = date(y, m, day_num).weekday()  # Mon=0 .. Sun=6
        gh_weekday = (weekday + 1) % 7  # convert to Sun=0 .. Sat=6

        if gh_weekday == 0 and any(c is not None for c in current_week):
            weeks.append(current_week)
            current_week = [None] * DAYS

        current_week[gh_weekday] = d

    if any(c is not None for c in current_week):
        weeks.append(current_week)

    # keep only the most recent WEEKS columns
    return weeks[-WEEKS:]


def build_svg(data: dict) -> str:
    weeks = bucket_into_weeks(data["days"])
    stats = data["stats"]

    grid_width = len(weeks) * (CELL + GAP)
    grid_height = DAYS * (CELL + GAP)
    total_width = LEFT_MARGIN + grid_width + 20
    total_height = TOP_MARGIN + grid_height + LEGEND_HEIGHT + FOOTER_HEIGHT

    cells_svg = []
    for wi, week in enumerate(weeks):
        begin = round(wi * STAGGER_PER_WEEK, 3)
        for di, day in enumerate(week):
            if day is None:
                continue
            level = min(day.get("level", 0), len(PALETTE) - 1)
            color = PALETTE[level]
            x = LEFT_MARGIN + wi * (CELL + GAP)
            y = TOP_MARGIN + di * (CELL + GAP)

            cells_svg.append(f"""
  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2"
        fill="{color}" opacity="0" transform="translate(-6,-6)">
    <title>{day['count']} contributions on {day['date']}</title>
    <animate attributeName="opacity" from="0" to="1"
             begin="{begin}s" dur="{CELL_DUR}s" fill="freeze" />
    <animateTransform attributeName="transform" type="translate"
             from="-6,-6" to="0,0"
             begin="{begin}s" dur="{CELL_DUR}s" fill="freeze" />
  </rect>""")

    legend_y = TOP_MARGIN + grid_height + 16
    legend_x_start = total_width - 20 - len(PALETTE) * (CELL + GAP) - 40
    legend_swatches = []
    for i, color in enumerate(PALETTE):
        x = legend_x_start + 30 + i * (CELL + GAP)
        legend_swatches.append(
            f'<rect x="{x}" y="{legend_y - CELL + 2}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}" />'
        )

    footer_y = total_height - 14
    footer_text = (
        f"{stats['total_contributions']:,} contributions in the last year "
        f"\u00b7 current streak {stats['current_streak']}d "
        f"\u00b7 longest streak {stats['longest_streak']}d"
    )

    svg = f"""<svg viewBox="0 0 {total_width} {total_height}" width="{total_width}" height="{total_height}"
     xmlns="http://www.w3.org/2000/svg">
  <rect width="{total_width}" height="{total_height}" fill="none" />
{"".join(cells_svg)}
  <text x="{legend_x_start}" y="{legend_y}" font-family="monospace" font-size="11" fill="#8b949e">Less</text>
{"".join(legend_swatches)}
  <text x="{legend_x_start + 40 + len(PALETTE) * (CELL + GAP) + 6}" y="{legend_y}"
        font-family="monospace" font-size="11" fill="#8b949e">More</text>
  <text x="{LEFT_MARGIN}" y="{footer_y}" font-family="monospace" font-size="12" fill="#8b949e">{footer_text}</text>
</svg>"""
    return svg


def main():
    data = load_data()
    svg = build_svg(data)
    with open("contrib-heatmap.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Wrote contrib-heatmap.svg")


if __name__ == "__main__":
    main()
