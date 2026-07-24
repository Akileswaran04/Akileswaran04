#!/usr/bin/env python3
"""Render data/contributions.json as a terminal-window contribution heatmap
SVG with a single SMIL-animated drone patrolling the bottom rail and shooting
upward at contribution cells.

System-critical terminal theme:
  bg  #0a0a0a  (near-black)
  txt #f5f5f5  (off-white)
  red #e10600  (single accent)
  gray         (muted lines)

Drone: sits on a horizontal rail at the bottom of the SVG, moves left→right
in one dimension.  For each column it passes, it fires a burst of bullets
upward at every non-zero cell in that column — one bullet per contribution
(capped at SHOTS_CAP to keep the SVG size sane).  Tooltips and stats always
show the real contribution count.
"""

import datetime
import json
import os
import random

random.seed(42)

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "contrib-heatmap.svg")

# ═══════════════════════════════════════════════════════════════════
#  SYSTEM-CRITICAL TERMINAL THEME  —  sharp, no competing colours
# ═══════════════════════════════════════════════════════════════════

PALETTE = [
    "#0a0a0a",   # 0  — invisible (matches bg)
    "#2d0a08",   # 1-5  — visible dark red
    "#5a1414",   # 6-15
    "#882020",   # 16-30
    "#b83030",   # 31-50
    "#e10600",   # 50+  — full accent
]

BG           = "#0a0a0a"
BG2          = "#111111"
FRAME        = "#e10600"
MUTED        = "#888888"
TEXT         = "#f5f5f5"
ACCENT       = "#e10600"
DRONE_COLOR  = "#e10600"
TRAIL_COLOR  = "#f5f5f5"
SHOTS_CAP    = 6           # max rendered shots per cell (tooltip + stats real)
SHOT_SPREAD  = 3           # horiz spread of bullets (pixels) for visual variety

CELL    = 12
GAP     = 3
STEP    = CELL + GAP
PAD     = 22
LEFT_LABEL_W = 30
TOP_LABEL_H  = 20
TITLEBAR_H   = 30
STATS_H      = 88
DRONE_RAIL_H = 50          # extra height for the drone track at bottom

DRONE_DELAY = 2.0          # seconds before drone starts
DRONE_DUR   = 18.0         # seconds for full left→right sweep (includes hold time)
HOLD_DUR    = 0.35         # seconds to hover at each column with contributions


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
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + STATS_H + PAD + DRONE_RAIL_H

    gx = PAD + LEFT_LABEL_W      # grid left edge
    gy = TITLEBAR_H + TOP_LABEL_H  # grid top

    # ── drone rail ─────────────────────────────────────────────────────
    stats_bottom_y = TITLEBAR_H + TOP_LABEL_H + art_h + STATS_H + PAD
    rail_y = stats_bottom_y + DRONE_RAIL_H / 2         # rail centre Y
    drone_cy = rail_y + 4                              # drone centre Y (slightly below centre of rail)

    # ──── CSS ──────────────────────────────────────────────────────────
    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
.c {{ opacity: 0; animation: cell 0.42s cubic-bezier(.2,.8,.2,1) both; }}
    """.strip()

    # ── build SVG ──────────────────────────────────────────────────────
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<style>{css}</style>',
        '<defs>'
        f'<linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>'
        '<filter id="glow"><feGaussianBlur stdDeviation="1.5" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '</defs>',
        # overall background
        f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{canvas_w-1}" height="{canvas_h-1}" rx="12" '
        f'fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        # title bar
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{canvas_w}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
        *[f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dotcol}"/>'
          for i, dotcol in enumerate(["#e10600", "#e10600", "#e10600"])],
        f'<text x="{canvas_w / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
        f'text-anchor="middle">{data["username"]}@github: ~/contributions --graph</text>',
    ]

    # month & weekday labels
    for ci, label in month_labels:
        parts.append(
            f'<text x="{gx + ci * STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" font-size="10">{label}</text>')
    for wi, wname in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(
            f'<text x="{PAD}" y="{gy + wi * STEP + CELL * 0.78:.1f}" fill="{MUTED}" font-size="9">{wname}</text>')

    # ──── contribution grid cells ─────────────────────────────────────
    grid_cells = []
    for ci, column in enumerate(grid):
        cx = gx + ci * STEP
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            cy = gy + ri * STEP
            delay = ci * 0.018 + ri * 0.045
            plural = "s" if count != 1 else ""
            grid_cells.append((ci, ri, cx, cy, date_s, count, lvl, delay))

    for (ci, ri, cx, cy, date_s, count, lvl, delay) in grid_cells:
        parts.append(
            f'<rect class="c" x="{cx}" y="{cy}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{PALETTE[lvl]}" style="animation-delay:{delay:.3f}s">'
            f'<title>{date_s}: {count} contribution{plural}</title></rect>'
        )

    # ──── drone rail track ────────────────────────────────────────────
    rail_left = gx
    rail_right = gx + n_cols * STEP
    parts.append(
        f'<line x1="{rail_left}" y1="{rail_y}" x2="{rail_right}" y2="{rail_y}" '
        f'stroke="{FRAME}" stroke-width="1" stroke-dasharray="4,4" stroke-opacity="0.25"/>'
    )

    # ──── stop-and-shoot: compute arrival time for each column ──────
    # Group cells by column
    col_cells = {ci: [] for ci in range(n_cols)}
    for (ci, ri, cx, cy, date_s, count, lvl, delay) in grid_cells:
        if count > 0:
            col_cells[ci].append((ri, cx, cy, count))

    # Compute column-centre positions and stop-and-shoot timings
    col_cx_list = [gx + ci * STEP + CELL / 2 for ci in range(n_cols)]
    n_pause = sum(1 for ci in range(n_cols) if col_cells[ci])
    move_time = max(DRONE_DUR - n_pause * HOLD_DUR, DRONE_DUR * 0.3)
    move_per_col = move_time / max(n_cols - 1, 1)

    col_arrival = [0.0] * n_cols   # absolute seconds from DRONE_DELAY
    cur_t = 0.0
    for ci in range(n_cols):
        if ci > 0:
            cur_t += move_per_col
        col_arrival[ci] = cur_t
        if col_cells[ci] and ci < n_cols - 1:
            cur_t += HOLD_DUR

    # Normalize so last arrival doesn't exceed DRONE_DUR
    total_time = cur_t if n_cols > 0 else DRONE_DUR
    if total_time > DRONE_DUR:
        scale = DRONE_DUR / total_time
        col_arrival = [t * scale for t in col_arrival]

    # Build stepped values/keyTimes for drone motion
    motion_vals = []
    motion_kts = []
    motion_vals.append(f"{col_cx_list[0]:.1f},{drone_cy:.1f}")
    motion_kts.append(0.0)
    for ci in range(n_cols):
        cx = col_cx_list[ci]
        arrive = col_arrival[ci]
        depart = arrive + (HOLD_DUR if col_cells[ci] and ci < n_cols - 1 else 0.0)
        arrive_frac = arrive / DRONE_DUR
        depart_frac = min(depart / DRONE_DUR, 1.0)
        if ci > 0:
            motion_vals.append(f"{cx:.1f},{drone_cy:.1f}")
            motion_kts.append(arrive_frac)
        if depart > arrive and depart_frac < 1.0:
            motion_vals.append(f"{cx:.1f},{drone_cy:.1f}")
            motion_kts.append(depart_frac)
    if motion_kts[-1] < 1.0:
        motion_kts.append(1.0)
        motion_vals.append(motion_vals[-1])

    # ──── bullets — fire during the hover window at each column ───────
    for ci in range(n_cols):
        if not col_cells[ci]:
            continue

        col_cx = col_cx_list[ci]
        # Fire mid-hover or on arrival (whichever has cells)
        shoot_base = DRONE_DELAY + col_arrival[ci]

        for ri, cell_cx, cell_cy, count in col_cells[ci]:
            n_shots = min(count, SHOTS_CAP)
            for s in range(n_shots):
                shot_dur = 0.15
                shot_offset = s * (0.12 / max(n_shots, 1))
                shot_at = shoot_base + shot_offset
                spread_x = (s - n_shots / 2) * 1.8 + random.uniform(-1, 1)
                start_x = col_cx + spread_x
                end_x = col_cx + spread_x * 0.3
                start_y = drone_cy
                end_y = cell_cy + CELL / 2

                parts.append(
                    f'<circle r="2.2" fill="{TRAIL_COLOR}" opacity="0">'
                    f'<animate attributeName="opacity" values="0;1;1;0" '
                    f'keyTimes="0;0.15;0.6;1" dur="{shot_dur:.2f}s" '
                    f'begin="{shot_at:.3f}s" fill="freeze"/>'
                    f'<animateMotion path="M{start_x:.1f},{start_y:.1f} L{end_x:.1f},{end_y:.1f}" '
                    f'dur="{shot_dur:.2f}s" begin="{shot_at:.3f}s" fill="freeze"/>'
                    f'</circle>'
                )

    # ──── impact flash on cells (white flash when hit) ────────────────
    for ci in range(n_cols):
        if not col_cells[ci]:
            continue
        shoot_base = DRONE_DELAY + col_arrival[ci]

        for ri, cell_cx, cell_cy, count in col_cells[ci]:
            orig_color = PALETTE[level_for(count)]
            parts.append(
                f'<rect x="{cell_cx}" y="{cell_cy}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{orig_color}">'
                f'<animate attributeName="fill" '
                f'values="{orig_color};{TRAIL_COLOR};{TRAIL_COLOR};{orig_color}" '
                f'keyTimes="0;0.12;0.45;1" dur="0.6s" begin="{shoot_base:.3f}s" fill="freeze"/>'
                f'</rect>'
            )

    # ──── drone sprite on a horizontal rail ───────────────────────────
    def drone_sprite():
        """Military attack quadcopter — centred at (0,0).
        Rotor discs with spinning blades, armoured fuselage,
        twin cannons, targeting sensor, and landing skids.
        """
        a = 7            # arm length from centre to rotor hub
        hub = 3.5        # rotor hub radius
        blade_len = 6.5  # visible blade length

        rotors = "".join(
            f'<g transform="translate({dx*a:.1f},{dy*a:.1f})">'
            # hub
            f'<circle r="{hub}" fill="none" stroke="{DRONE_COLOR}" stroke-width="1.0" opacity="0.7"/>'
            # spinning blade cross
            f'<g opacity="0.6">'
            f'<line x1="-{blade_len}" y1="0" x2="{blade_len}" y2="0" stroke="{DRONE_COLOR}" '
            f'stroke-width="1.6" stroke-linecap="round"/>'
            f'<line x1="0" y1="-{blade_len}" x2="0" y2="{blade_len}" stroke="{DRONE_COLOR}" '
            f'stroke-width="1.6" stroke-linecap="round"/>'
            f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" '
            f'dur="0.25s" repeatCount="indefinite"/></g></g>'
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        )

        # rotor arm booms (X-frame connecting hubs to body)
        arms = "".join(
            f'<line x1="{dx*a*0.5:.1f}" y1="{dy*a*0.5:.1f}" x2="{dx*a:.1f}" y2="{dy*a:.1f}" '
            f'stroke="{DRONE_COLOR}" stroke-width="0.8" opacity="0.4"/>'
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]
        )

        # fuselage (armoured body — hexagon shape)
        fuselage = (
            f'<polygon points="0,-1.5 -4.5,-0.5 -4.5,2.5 0,4 4.5,2.5 4.5,-0.5" '
            f'fill="{BG}" stroke="{DRONE_COLOR}" stroke-width="1.2" stroke-linejoin="round"/>'
            # armoured plating line
            f'<line x1="-3" y1="0" x2="3" y2="0" stroke="{DRONE_COLOR}" '
            f'stroke-width="0.6" opacity="0.5"/>'
        )

        # targeting sensor (camera ball under belly)
        sensor = (
            f'<circle cx="0" cy="2.8" r="2.2" fill="{DRONE_COLOR}" opacity="0.9"/>'
            f'<circle cx="0" cy="2.8" r="1.0" fill="{BG}"/>'
            f'<circle cx="0.4" cy="2.5" r="0.35" fill="{DRONE_COLOR}"/>'
        )

        # twin cannons (weapon barrels pointing upward, symmetric, mounted into body)
        barrel_w = 1.8
        l_cannon = -2.8          # left cannon center
        r_cannon = 2.8           # right cannon center
        cannons = (
            f'<rect x="{l_cannon - barrel_w/2:.1f}" y="-8" width="{barrel_w}" height="6.5" '
            f'rx="0.6" fill="{DRONE_COLOR}"/>'
            f'<rect x="{r_cannon - barrel_w/2:.1f}" y="-8" width="{barrel_w}" height="6.5" '
            f'rx="0.6" fill="{DRONE_COLOR}"/>'
            # muzzle flash at cannon tips (bright white to match bullets)
            f'<rect x="{l_cannon - 0.5:.1f}" y="-10" width="1.0" height="2.5" '
            f'rx="0.3" fill="{TRAIL_COLOR}" opacity="0.85"/>'
            f'<rect x="{r_cannon - 0.5:.1f}" y="-10" width="1.0" height="2.5" '
            f'rx="0.3" fill="{TRAIL_COLOR}" opacity="0.85"/>'
        )

        # tail antenna
        antenna = (
            f'<line x1="0" y1="-1.5" x2="0" y2="-10.5" stroke="{DRONE_COLOR}" '
            f'stroke-width="0.7" opacity="0.5"/>'
            f'<circle cx="0" cy="-10.5" r="0.8" fill="{DRONE_COLOR}" opacity="0.7"/>'
        )

        # landing skids
        skids = (
            f'<line x1="-3.5" y1="4" x2="-5" y2="7" stroke="{DRONE_COLOR}" '
            f'stroke-width="0.8" opacity="0.5" stroke-linecap="round"/>'
            f'<line x1="3.5" y1="4" x2="5" y2="7" stroke="{DRONE_COLOR}" '
            f'stroke-width="0.8" opacity="0.5" stroke-linecap="round"/>'
            f'<line x1="-6" y1="7" x2="6" y2="7" stroke="{DRONE_COLOR}" '
            f'stroke-width="0.8" opacity="0.4" stroke-linecap="round"/>'
        )

        return rotors + arms + fuselage + sensor + cannons + antenna + skids

    # ──── stepped drone motion: stop-and-shoot ────────────────────────
    path_y = drone_cy

    parts.append(
        f'<g opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="0.4s" '
        f'begin="{DRONE_DELAY:.2f}s" fill="freeze"/>'
        f'{drone_sprite()}'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values={"; ".join(motion_vals)} '
        f'keyTimes={"; ".join(f"{t:.4f}" for t in motion_kts)} '
        f'dur="{DRONE_DUR:.2f}s" begin="{DRONE_DELAY:.3f}s" fill="freeze"/>'
        f'</g>'
    )

    # ──── final pulse on last cell ────────────────────────────────────
    last_col = n_cols - 1
    last_arrival = DRONE_DELAY + col_arrival[n_cols - 1]
    pulse_start = last_arrival + 0.1
    for ri, cell_cx, cell_cy, count in col_cells.get(last_col, []):
        pcx = cell_cx + CELL / 2
        pcy = cell_cy + CELL / 2
        parts.append(
            f'<circle cx="{pcx:.1f}" cy="{pcy:.1f}" r="3" fill="{DRONE_COLOR}" '
            f'filter="url(#glow)" opacity="0">'
            f'<animate attributeName="r" values="3;16;18" keyTimes="0;0.4;1" '
            f'dur="1.4s" begin="{pulse_start:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;1.0;0" keyTimes="0;0.2;1" '
            f'dur="1.4s" begin="{pulse_start:.3f}s" fill="freeze"/>'
            f'</circle>'
        )

    # ──── legend ──────────────────────────────────────────────────────
    leg_y = gy + art_h + 6
    leg_x = canvas_w - PAD - (len(PALETTE) * (CELL - 1) + 70)
    parts.append(
        f'<text x="{leg_x}" y="{leg_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for color in PALETTE:
        parts.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL - 1}" height="{CELL - 1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{leg_y + CELL * 0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    # ──── separator ───────────────────────────────────────────────────
    sep_y = leg_y + CELL + 14
    parts.append(
        f'<line x1="0" y1="{sep_y}" x2="{canvas_w}" y2="{sep_y}" stroke="{FRAME}" stroke-opacity="0.25"/>')

    # ──── stats ───────────────────────────────────────────────────────
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    total = data["total_contributions"]
    best = data["best_day"]
    rng = data["range"]

    ly = sep_y + 24
    parts.append(
        f'<text x="{PAD}" y="{ly}" font-size="13" fill="{ACCENT}">'
        f'<tspan font-weight="700">{total:,}</tspan>'
        f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    parts.append(
        f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
        f'{rng["start"]} → {rng["end"]}</text>')
    ly += 24
    parts.append(
        f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
        f'<tspan fill="{ACCENT}" font-weight="700">{cs} days</tspan>'
        f'<tspan fill="{MUTED}">   ·   longest </tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{ls} days</tspan></text>')
    parts.append(
        f'<text x="{canvas_w - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
        f'best day <tspan fill="{ACCENT}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')

    # ──── bottom rail label ───────────────────────────────────────────
    rail_label_y = stats_bottom_y + DRONE_RAIL_H - 8
    parts.append(
        f'<text x="{canvas_w / 2}" y="{rail_label_y}" font-size="10" fill="{MUTED}" '
        f'text-anchor="middle" opacity="0.5">'
        f'[ drone sweep — firing {SHOTS_CAP} rounds max per cell ]</text>')

    # ──── blinking terminal cursor at bottom ──────────────────────────
    cursor_x = canvas_w - PAD
    cursor_y = rail_label_y
    parts.append(
        f'<rect x="{cursor_x}" y="{cursor_y - 10}" width="7" height="13" fill="{ACCENT}" opacity="0.7">'
        f'<animate attributeName="opacity" values="0.7;0.7;0;0" '
        f'keyTimes="0;0.45;0.5;1" dur="1s" repeatCount="indefinite"/></rect>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
