"""
make_info_card.py — hand-authored neofetch-style SVG panel.
Each line fades + slides in on a short stagger. Set STATIC=1 to emit a
frozen (already-visible) frame, handy for local Quick Look previews.

Usage:
    python scripts/make_info_card.py
    STATIC=1 python scripts/make_info_card.py

Output:
    info-card.svg
"""

import os

# ---- Edit these to describe yourself -------------------------------------
USERNAME = "stadlxr"
TITLE_BAR = f"{USERNAME}@github: ~"
ROWS = [
    ("Now", "LFW & Freelancing"),
    ("Exp", "Junior Software Engineer"),
    ("Stack", "Java · HTML CSS JS · React · PHP"),
    ("Highlights", "BSc IT - Software Engineer, Golden Key"),
]
# ----------------------------------------------------------------------------

WIDTH = 490
ROW_HEIGHT = 34
HEADER_HEIGHT = 40
PADDING = 20

BG = "#0d1117"
BAR_BG = "#161b22"
TEXT_DIM = "#8b949e"
TEXT_KEY = "#58a6ff"
TEXT_VAL = "#c9d1d9"
BORDER = "#30363d"

STAGGER = 0.18
DUR = 0.4

STATIC = os.environ.get("STATIC") == "1"


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def row_group(i: int, key: str, value: str) -> str:
    y = HEADER_HEIGHT + PADDING + i * ROW_HEIGHT
    begin = round(i * STAGGER, 3)

    if STATIC:
        opacity_attr = 'opacity="1"'
        transform_attr = ""
        animation = ""
    else:
        opacity_attr = 'opacity="0"'
        transform_attr = f'transform="translate(-12,0)"'
        animation = f"""
        <animate attributeName="opacity" from="0" to="1"
                 begin="{begin}s" dur="{DUR}s" fill="freeze" />
        <animateTransform attributeName="transform" type="translate"
                 from="-12,0" to="0,0"
                 begin="{begin}s" dur="{DUR}s" fill="freeze" />"""

    return f"""
  <g {opacity_attr} {transform_attr}>{animation}
    <text x="{PADDING}" y="{y}" font-family="monospace" font-size="14"
          font-weight="bold" fill="{TEXT_KEY}">{escape_xml(key)}</text>
    <text x="{PADDING + 110}" y="{y}" font-family="monospace" font-size="14"
          fill="{TEXT_VAL}">{escape_xml(value)}</text>
  </g>"""


def build_svg() -> str:
    height = HEADER_HEIGHT + PADDING * 2 + len(ROWS) * ROW_HEIGHT

    rows_svg = "".join(row_group(i, k, v) for i, (k, v) in enumerate(ROWS))

    return f"""<svg viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" height="{height}"
     xmlns="http://www.w3.org/2000/svg">
  <rect width="{WIDTH}" height="{height}" rx="8" fill="{BG}" stroke="{BORDER}" />
  <rect width="{WIDTH}" height="{HEADER_HEIGHT}" rx="8" fill="{BAR_BG}" />
  <rect y="{HEADER_HEIGHT - 8}" width="{WIDTH}" height="8" fill="{BAR_BG}" />
  <circle cx="20" cy="{HEADER_HEIGHT / 2}" r="6" fill="#ff5f56" />
  <circle cx="40" cy="{HEADER_HEIGHT / 2}" r="6" fill="#ffbd2e" />
  <circle cx="60" cy="{HEADER_HEIGHT / 2}" r="6" fill="#27c93f" />
  <text x="{WIDTH / 2}" y="{HEADER_HEIGHT / 2 + 5}" text-anchor="middle"
        font-family="monospace" font-size="13" fill="{TEXT_DIM}">{escape_xml(TITLE_BAR)}</text>
{rows_svg}
</svg>"""


def main():
    svg = build_svg()
    with open("info-card.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Wrote info-card.svg" + (" (static frame)" if STATIC else ""))


if __name__ == "__main__":
    main()
