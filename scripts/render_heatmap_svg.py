#!/usr/bin/env python3
"""
Render data/contributions.json (produced by fetch_contributions.py) as a proper
GitHub-style contribution heatmap SVG with a terminal-window card and an
integrated snake animation that eats through the grid.

The snake traces a serpentine path through all contribution squares using SMIL
animations — no JavaScript needed. The snake head is a glowing rounded rect
that animates x/y through every grid cell, and each cell briefly flashes to
bright green as the snake "eats" it, then settles back to its contribution
intensity level.
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# ── Color palette ─────────────────────────────────────────────────────
# 5 contribution intensity greens + an extra brightest for the snake glow
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#4ade80"]
SNAKE_COLOR = "#4ade80"
EATEN_FLASH = "#69f0a0"

BG      = "#0a0e14"
BG2     = "#0d1420"
FRAME   = "#1f6feb"
MUTED   = "#7d8590"
TEXT    = "#e6edf3"
ACCENT  = "#22d3ee"
GREEN   = "#39d353"
GOLD    = "#f2cc60"

CELL      = 12
GAP       = 3
STEP      = CELL + GAP
PAD       = 22
LEFT_LABEL_W = 30
TOP_LABEL_H  = 20
TITLEBAR_H   = 30

STATS_H = 88

# ── Snake animation timing ─────────────────────────────────────────────
SNAKE_DELAY     = 1.8    # wait for cells to appear before snake starts
SNAKE_DUR       = 8.0    # total time for snake to traverse all cells
SNAKE2_OFFSET   = 1.8    # second snake start delay after first
SNAKE2_COLOR    = "#22d3ee"  # cyan accent for second snake
CELL_EAT_DUR    = 0.4   # brief flash duration per cell when snake eats it
CELL_EAT_BEGIN  = 0.1   # flash starts at this fraction of CELL_EAT_DUR
CELL_EAT_END    = 0.6   # flash fades back by this fraction of CELL_EAT_DUR

# ── Helpers ────────────────────────────────────────────────────────────
def level_for(count):
    if count == 0:  return 0
    if count <= 5:  return 1
    if count <= 15: return 2
    if count <= 30: return 3
    if count <= 50: return 4
    return 5

def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7  # sunday=0
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid

def build_snake_path(grid, grid_left, grid_top):
    """
    Build a serpentine path through non-None grid cells only.
    Odd columns go bottom→top, even columns go top→bottom.
    Returns (positions, cell_data) where:
      - positions: list of (x, y) pixel coords for the snake head
      - cell_data: list of (date, count, lvl) matching each position
    """
    positions = []
    cell_data = []
    for ci, column in enumerate(grid):
        if ci % 2 == 0:
            rows_range = range(7)
        else:
            rows_range = range(6, -1, -1)
        for ri in rows_range:
            cell = column[ri]
            if cell is None:
                continue
            x = grid_left + ci * STEP
            y = grid_top + ri * STEP
            positions.append((x, y))
            cell_data.append(cell)
    return positions, cell_data

def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    # ── Month labels ────────────────────────────────────────────────
    month_labels = []
    seen_months = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + STATS_H + PAD

    # ── CSS: cell fade-in ──────────────────────────────────────────
    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.c {{ opacity: 0; animation: cell 0.42s cubic-bezier(.2,.8,.2,1) both; }}
""".strip()

    # ── Build the snake path (only non-None cells, in serpentine order) ──
    grid_left = PAD + LEFT_LABEL_W
    grid_top  = TITLEBAR_H + TOP_LABEL_H
    snake_path, snake_cells = build_snake_path(grid, grid_left, grid_top)
    n_cells = len(snake_path)

    # ── SVG assembly ──────────────────────────────────────────────
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>'
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        f'<filter id="snake-glow"><feGaussianBlur stdDeviation="2" result="blur"/>'
        f'<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '</defs>',
        # Card background
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" '
        f'stroke="{FRAME}" stroke-opacity="0.35"/>',
        # macOS dots
        *[f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{dotcol}"/>'
          for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])],
        # Title
        f'<text x="{canvas_w/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">{data["username"]}@github: ~/contributions --graph</text>',
    ]

    # ── Month labels ──────────────────────────────────────────────
    for ci, label in month_labels:
        x = grid_left + ci * STEP
        parts.append(f'<text x="{x}" y="{TITLEBAR_H + 14}" fill="{MUTED}" '
                     f'font-size="10">{label}</text>')

    # ── Weekday labels ────────────────────────────────────────────
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = grid_top + wi * STEP + CELL * 0.78
        parts.append(f'<text x="{PAD}" y="{y:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    # ── Contribution grid cells ──
    for ci, column in enumerate(grid):
        gx = grid_left + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            gy = grid_top + ri * STEP
            delay = ci * 0.018 + ri * 0.045
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="c" x="{gx}" y="{gy}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{PALETTE[lvl]}" '
                f'style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>'
            )

    # ── Legend: Less [][][][][] More ──────────────────────────────
    leg_y = grid_top + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" '
                 f'font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" '
                     f'rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" '
                 f'font-size="10">More</text>')

    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" '
                 f'stroke="{FRAME}" stroke-opacity="0.25"/>')

    # ── Stats rows ────────────────────────────────────────────────
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}">'
                 f'<tspan font-weight="700">{total:,}</tspan>'
                 f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" '
                 f'text-anchor="end">{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
                 f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>'
                 f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
                 f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" '
                 f'text-anchor="end">best day <tspan fill="{GOLD}" font-weight="700">'
                 f'{best["count"]}</tspan> on {best["date"]}</text>')

    # ── SNAKE ANIMATION ──────────────────────────────────────────
    # Build keyTimes and values strings for the SMIL animate attributes.
    key_times = [f"{i / max(n_cells - 1, 1):.4f}" for i in range(n_cells)]
    kt_str  = ";".join(key_times)
    snake_size = CELL + 2
    head_offset = (snake_size - CELL) / 2
    x_vals_offset = ";".join(str(p[0] - head_offset) for p in snake_path)
    y_vals_offset = ";".join(str(p[1] - head_offset) for p in snake_path)

    def make_snake(color, delay_offset):
        return (
            f'<rect x="{snake_path[0][0] - head_offset}" '
            f'y="{snake_path[0][1] - head_offset}" '
            f'width="{snake_size}" height="{snake_size}" rx="3.5" '
            f'fill="{color}" filter="url(#snake-glow)" opacity="0">\n'
            f'  <animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay_offset:.1f}s" dur="0.01s" fill="freeze"/>\n'
            f'  <animate attributeName="x" values="{x_vals_offset}" '
            f'keyTimes="{kt_str}" '
            f'begin="{delay_offset:.1f}s" dur="{SNAKE_DUR:.1f}s" fill="freeze"/>\n'
            f'  <animate attributeName="y" values="{y_vals_offset}" '
            f'keyTimes="{kt_str}" '
            f'begin="{delay_offset:.1f}s" dur="{SNAKE_DUR:.1f}s" fill="freeze"/>\n'
            f'  <animate attributeName="opacity" from="1" to="0" '
            f'begin="{delay_offset + SNAKE_DUR:.1f}s" dur="0.01s" fill="freeze"/>'
            f'</rect>'
        )

    parts.append(make_snake(SNAKE_COLOR, SNAKE_DELAY))
    parts.append(make_snake(SNAKE2_COLOR, SNAKE_DELAY + SNAKE2_OFFSET))

    # ── Cell eaten flash overlays (in snake-path order) ────────────
    # Each cell briefly flashes the matching snake's color when the snake
    # passes over, then returns to its original contribution intensity.
    # Green flash (snake 1) + cyan flash (snake 2)
    for i, (cx, cy) in enumerate(snake_path):
        _date, _count, lvl = snake_cells[i]
        arrive  = SNAKE_DELAY + i * SNAKE_DUR / max(n_cells - 1, 1)
        arrive2 = SNAKE_DELAY + SNAKE2_OFFSET + i * SNAKE_DUR / max(n_cells - 1, 1)
        orig_color = PALETTE[lvl]
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{orig_color}">\n'
            f'  <animate attributeName="fill" '
            f'values="{orig_color};{EATEN_FLASH};{EATEN_FLASH};{orig_color}" '
            f'keyTimes="0;{CELL_EAT_BEGIN:.3f};{CELL_EAT_END:.3f};1" '
            f'dur="{CELL_EAT_DUR:.2f}s" '
            f'begin="{arrive:.3f}s" fill="freeze"/>\n'
            f'  <animate attributeName="fill" '
            f'values="{orig_color};{SNAKE2_COLOR};{SNAKE2_COLOR};{orig_color}" '
            f'keyTimes="0;{CELL_EAT_BEGIN:.3f};{CELL_EAT_END:.3f};1" '
            f'dur="{CELL_EAT_DUR:.2f}s" '
            f'begin="{arrive2:.3f}s" fill="freeze"/>\n'
            f'</rect>'
        )

    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
