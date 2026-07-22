#!/usr/bin/env python3
"""Render data/contributions.json as a terminal-window contribution heatmap
SVG with two SMIL-animated snakes (emerald tide, yin-yang flow).

Snake 1 (emerald #34d399): forward serpentine through grid columns.
Snake 2 (jade #059669): reverse serpentine (start at last cell, go backward).
Both leave a brief flash trail when passing through each cell.
"""

import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#4ade80"]

BG      = "#0a0e14"
BG2     = "#0d1420"
FRAME   = "#1f6feb"
MUTED   = "#7d8590"
TEXT    = "#e6edf3"
ACCENT  = "#34d399"
GREEN   = "#39d353"
GOLD    = "#f2cc60"
SNAKE_COLOR  = "#34d399"
SNAKE2_COLOR = "#059669"
EATEN_FLASH  = "#6ee7b7"

CELL    = 12
GAP     = 3
STEP    = CELL + GAP
PAD     = 22
LEFT_LABEL_W = 30
TOP_LABEL_H  = 20
TITLEBAR_H   = 30
STATS_H = 88
SNAKE_DELAY    = 1.5      # seconds before snake starts
SNAKE_DUR      = 6.0      # seconds for full traversal
CELL_EAT_DUR   = 0.35     # seconds for cell flash animation
HEAD_R         = 5        # snake head circle radius


def level_for(count):
    if count == 0:  return 0
    if count <= 5:  return 1
    if count <= 15: return 2
    if count <= 30: return 3
    if count <= 50: return 4
    return 5


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7
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
    """Build a serpentine path visiting every non-None cell in column order.
    Returns (positions, cells) lists in visitation order.
    """
    positions = []
    cells = []
    for ci, column in enumerate(grid):
        rng = range(len(column))
        if ci % 2 == 1:
            rng = reversed(rng)
        for ri in rng:
            cell = column[ri]
            if cell is None:
                continue
            cx = grid_left + ci * STEP
            cy = grid_top + ri * STEP
            positions.append((cx, cy))
            cells.append(cell)
    return positions, cells


def render(data):
    days = data["days"]
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

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

    gx = PAD + LEFT_LABEL_W
    gy = TITLEBAR_H + TOP_LABEL_H

    snake_path, snake_cells = build_snake_path(grid, gx, gy)
    rev_path = list(reversed(snake_path))
    n_cells = len(snake_path)
    if n_cells < 2:
        n_cells = 2  # avoid division by zero

    # ---- timing helpers ----
    def timing(i):
        return SNAKE_DELAY + i * SNAKE_DUR / (n_cells - 1)

    # ---- build snake head keyframes ----
    xs_vals = ";".join(f"{p[0]}" for p in snake_path)
    ys_vals = ";".join(f"{p[1]}" for p in snake_path)
    rev_xs  = ";".join(f"{p[0]}" for p in rev_path)
    rev_ys  = ";".join(f"{p[1]}" for p in rev_path)
    kt_vals = ";".join(f"{i / (n_cells - 1):.6f}" for i in range(n_cells))

    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.c {{ opacity: 0; animation: cell 0.42s cubic-bezier(.2,.8,.2,1) both; }}
.snake-head {{ opacity: 0; animation: snake-fade 0.3s {SNAKE_DELAY}s both; }}
@keyframes snake-fade {{ 0%{{opacity:0}} 100%{{opacity:1}} }}
    """.strip()

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        '<filter id="glow"><feGaussianBlur stdDeviation="1.5" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '</defs>',
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
        *[f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dotcol}"/>'
          for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"])],
        f'<text x="{canvas_w / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">{data["username"]}@github: ~/contributions --graph</text>',
    ]

    for ci, label in month_labels:
        parts.append(f'<text x="{gx + ci * STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="{PAD}" y="{gy + wi * STEP + CELL * 0.78:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    # ---- contribution grid cells ----
    for ci, column in enumerate(grid):
        cx = gx + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            cy = gy + ri * STEP
            delay = ci * 0.018 + ri * 0.045
            plural = "s" if count != 1 else ""
            parts.append(
                f'<rect class="c" x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_s}: {count} contribution{plural}</title></rect>'
            )

    # ---- cell flash overlays (position-based lookup) ----
    pos_idx_forward = {(cx, cy): i for i, (cx, cy) in enumerate(snake_path)}
    pos_idx_reverse = {(cx, cy): i for i, (cx, cy) in enumerate(rev_path)}
    positions_all = {(cx, cy): cell[2] for (cx, cy), cell in zip(snake_path, snake_cells)}

    for (cx, cy), orig_lvl in positions_all.items():
        i1 = pos_idx_forward.get((cx, cy))
        i2 = pos_idx_reverse.get((cx, cy))
        if i1 is None or i2 is None:
            continue
        orig_color = PALETTE[orig_lvl]
        a1 = timing(i1)
        a2 = timing(i2)
        parts.append(
            f'<rect x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2.5" fill="{orig_color}">'
            f'<animate attributeName="fill" values="{orig_color};{EATEN_FLASH};{EATEN_FLASH};{orig_color}" '
            f'keyTimes="0;0.15;0.65;1" dur="{CELL_EAT_DUR:.2f}s" begin="{a1:.3f}s" fill="freeze"/>'
            f'<animate attributeName="fill" values="{orig_color};{EATEN_FLASH};{EATEN_FLASH};{orig_color}" '
            f'keyTimes="0;0.15;0.65;1" dur="{CELL_EAT_DUR:.2f}s" begin="{a2:.3f}s" fill="freeze"/>'
            f'</rect>'
        )

    # ---- snake head 1 (forward, emerald) ----
    hx1 = snake_path[0][0]
    hy1 = snake_path[0][1]
    # glow filter is already inside <defs> above

    parts.append(
        f'<circle class="snake-head" cx="{hx1}" cy="{hy1}" r="{HEAD_R}" fill="{SNAKE_COLOR}" filter="url(#glow)">'
        f'<animate attributeName="cx" values="{xs_vals}" keyTimes="{kt_vals}" '
        f'dur="{SNAKE_DUR:.1f}s" begin="{SNAKE_DELAY:.3f}s" fill="freeze"/>'
        f'<animate attributeName="cy" values="{ys_vals}" keyTimes="{kt_vals}" '
        f'dur="{SNAKE_DUR:.1f}s" begin="{SNAKE_DELAY:.3f}s" fill="freeze"/>'
        f'</circle>'
    )

    # ---- snake head 2 (reverse, jade) ----
    hx2 = rev_path[0][0]
    hy2 = rev_path[0][1]
    parts.append(
        f'<circle class="snake-head" cx="{hx2}" cy="{hy2}" r="{HEAD_R}" fill="{SNAKE2_COLOR}" filter="url(#glow)">'
        f'<animate attributeName="cx" values="{rev_xs}" keyTimes="{kt_vals}" '
        f'dur="{SNAKE_DUR:.1f}s" begin="{SNAKE_DELAY:.3f}s" fill="freeze"/>'
        f'<animate attributeName="cy" values="{rev_ys}" keyTimes="{kt_vals}" '
        f'dur="{SNAKE_DUR:.1f}s" begin="{SNAKE_DELAY:.3f}s" fill="freeze"/>'
        f'</circle>'
    )

    # ---- legend ----
    leg_y = gy + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(f'<text x="{leg_x}" y="{leg_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL - 1}" height="{CELL - 1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    # ---- separator ----
    sep_y = leg_y + CELL + 14
    parts.append(f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

    # ---- stats ----
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{GREEN}">'
                 f'<tspan font-weight="700">{total:,}</tspan>'
                 f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    parts.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
                 f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>'
                 f'<tspan fill="{MUTED}">   &#183;   longest </tspan>'
                 f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    parts.append(f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
