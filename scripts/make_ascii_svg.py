"""
make_ascii_svg.py — downsample source-prepped.png to a character grid and
emit a monochrome ASCII-art SVG that "types" itself in, row by row,
via SMIL clip-path animation. Prints once, then freezes (no looping).

Usage:
    python scripts/make_ascii_svg.py

Output:
    avi-ascii.svg
"""

from PIL import Image

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

GRID_COLS = 100
GRID_ROWS = 53

CHAR_W = 6.6   # px per character cell, horizontal
CHAR_H = 12    # px per character cell, vertical
FONT_SIZE = 12
FILL_COLOR = "#9aa5b1"   # single light-gray fill -- monochrome on purpose
BG_COLOR = "none"

STAGGER_PER_ROW = 0.045   # seconds between each row starting its wipe
WIPE_DURATION = 0.35      # seconds for a single row's left-to-right wipe


def load_and_downsample(path: str) -> Image.Image:
    img = Image.open(path).convert("L")
    return img.resize((GRID_COLS, GRID_ROWS), Image.LANCZOS)


def pixel_to_char(value: int) -> str:
    # value: 0 (black) .. 255 (white). Map white -> sparse end, black -> dense end.
    idx = int((255 - value) / 255 * (len(RAMP) - 1))
    return RAMP[idx]


def image_to_rows(img: Image.Image) -> list[str]:
    pixels = img.load()
    rows = []
    for y in range(GRID_ROWS):
        row_chars = [pixel_to_char(pixels[x, y]) for x in range(GRID_COLS)]
        rows.append("".join(row_chars).rstrip() or " ")
    return rows


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(rows: list[str]) -> str:
    width = GRID_COLS * CHAR_W
    height = GRID_ROWS * CHAR_H

    defs = []
    text_els = []

    for i, row in enumerate(rows):
        row_width = len(row) * CHAR_W
        clip_id = f"clip{i}"
        start = round(i * STAGGER_PER_ROW, 3)
        end = round(start + WIPE_DURATION, 3)

        # clipPath rect animates its width from 0 -> full row width
        defs.append(f"""
    <clipPath id="{clip_id}">
      <rect x="0" y="{i * CHAR_H}" width="0" height="{CHAR_H + 2}">
        <animate attributeName="width" from="0" to="{row_width}"
                 begin="{start}s" dur="{WIPE_DURATION}s"
                 fill="freeze" calcMode="linear" />
      </rect>
    </clipPath>""")

        y_baseline = i * CHAR_H + CHAR_H * 0.8
        text_els.append(
            f'  <g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{y_baseline}" font-family="monospace" '
            f'font-size="{FONT_SIZE}" fill="{FILL_COLOR}" '
            f'xml:space="preserve">{escape_xml(row)}</text>'
            f"</g>"
        )
        # small "cursor" block riding the wipe edge, disappears once row is done
        text_els.append(
            f'  <rect width="{CHAR_W}" height="{CHAR_H}" y="{i * CHAR_H}" '
            f'fill="{FILL_COLOR}" opacity="0">'
            f'<animate attributeName="x" from="0" to="{max(row_width - CHAR_W, 0)}" '
            f'begin="{start}s" dur="{WIPE_DURATION}s" fill="freeze" calcMode="linear" />'
            f'<animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.01;0.9;1" begin="{start}s" dur="{WIPE_DURATION}s" fill="freeze" />'
            f"</rect>"
        )

    svg = f"""<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg">
  <defs>{"".join(defs)}
  </defs>
  <rect width="{width}" height="{height}" fill="{BG_COLOR}" />
{chr(10).join(text_els)}
</svg>"""
    return svg


def main():
    img = load_and_downsample("source-prepped.png")
    rows = image_to_rows(img)
    svg = build_svg(rows)
    with open("avi-ascii.svg", "w") as f:
        f.write(svg)
    print("Wrote avi-ascii.svg")


if __name__ == "__main__":
    main()
