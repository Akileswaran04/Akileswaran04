#!/usr/bin/env python3
"""Generate a streak-stats SVG card from contributions.json data.

Output: ../streak-stats.svg
Replaces the external streak-stats.demolab.com service with a local SVG
that always loads and always matches your actual data.

Cyber Cyan theme (matching contrib-heatmap):
  bg  #0d1117   bg2 #0f172a
  acc #22D3EE   mut #38BDF8   txt #e6edf3   dim #7d8590
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "streak-stats.svg")

# ═══════════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════════

BG     = "#0d1117"
BG2    = "#0f172a"
ACCENT = "#22D3EE"
MUTED  = "#38BDF8"
TEXT   = "#e6edf3"
DIM    = "#7d8590"
GREEN  = "#34D399"

W      = 860
H      = 200

TITLE_H = 30
PAD     = 30

RING_R    = 68       # ring radius
RING_CX   = 90       # ring centre X
RING_CY   = 115      # ring centre Y
RING_W    = 6        # ring stroke width

# Unicode characters (must be valid in XML, unlike HTML entities)
ARROW  = "\u2192"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(data):
    cs = data["current_streak"]
    ls = data["longest_streak"]
    bd = data["best_day"]
    total = data["total_contributions"]
    rng = data["range"]

    now = datetime.datetime.now(datetime.timezone.utc)
    gen_label = now.strftime("%Y-%m-%d %H:%M UTC")

    cs_label = f"{cs['length']} day{'s' if cs['length'] != 1 else ''}"
    ls_label = f"{ls['length']} day{'s' if ls['length'] != 1 else ''}"

    # Fire ring fill fraction (current streak vs longest)
    ring_frac = min(cs["length"] / max(ls["length"], 1), 1.0)
    circ = 2 * 3.14159265 * RING_R
    filled = circ * ring_frac
    empty  = circ - filled

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"',
        f'viewBox="0 0 {W} {H}"',
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',

        # ── Defs ──
        '<defs>',
        f'<linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/>',
        f'<stop offset="1" stop-color="{BG}"/></linearGradient>',
        f'<linearGradient id="ring-grad" x1="0" y1="0" x2="1" y2="0">',
        f'<stop offset="0" stop-color="{ACCENT}"/>',
        f'<stop offset="1" stop-color="{MUTED}"/></linearGradient>',
        '</defs>',

        # ── Background ──
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#sbg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12"',
        f'fill="none" stroke="{ACCENT}" stroke-width="1" stroke-opacity="0.55"/>',

        # ── Title bar ──
        f'<line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}"',
        f'stroke="{ACCENT}" stroke-opacity="0.35"/>',
        f'<circle cx="{PAD}" cy="{TITLE_H/2}" r="5" fill="{ACCENT}"/>',
        f'<circle cx="{PAD+16}" cy="{TITLE_H/2}" r="5" fill="{ACCENT}"/>',
        f'<circle cx="{PAD+32}" cy="{TITLE_H/2}" r="5" fill="{ACCENT}"/>',
        f'<text x="{W/2}" y="{TITLE_H/2+4}" fill="{MUTED}" font-size="12"',
        f'text-anchor="middle">akileswaran04@github: ~/streak-stats</text>',

        # ── Ring (background) ──
        f'<circle cx="{RING_CX}" cy="{RING_CY}" r="{RING_R}"',
        f'fill="none" stroke="{DIM}" stroke-width="{RING_W}" stroke-opacity="0.2"/>',

        # ── Ring (filled arc) ──
        f'<circle cx="{RING_CX}" cy="{RING_CY}" r="{RING_R}"',
        f'fill="none" stroke="url(#ring-grad)" stroke-width="{RING_W}"',
        f'stroke-linecap="round"',
        f'stroke-dasharray="{filled:.1f} {empty:.1f}"',
        f'transform="rotate(-90 {RING_CX} {RING_CY})"/>',

        # ── Ring centre text ──
        f'<text x="{RING_CX}" y="{RING_CY - 10}" text-anchor="middle"',
        f'fill="{ACCENT}" font-size="32" font-weight="700">{cs["length"]}</text>',
        f'<text x="{RING_CX}" y="{RING_CY + 14}" text-anchor="middle"',
        f'fill="{MUTED}" font-size="12">day streak</text>',
    ]

    # Glow dot at top of ring (decorative)
    if cs["length"] > 0:
        parts.append(
f'<circle cx="{RING_CX}" cy="{RING_CY - RING_R}" r="4" '
f'fill="{ACCENT}" opacity="0.6">'
f'<animate attributeName="opacity" values="0.3;1;0.3" '
f'dur="2s" repeatCount="indefinite"/>'
            f'</circle>'
        )

    # ── Stats columns ──
    col1_x = RING_CX + RING_R + 50
    col2_x = col1_x + 220

    # Total contributions
    parts.extend([
        f'<text x="{col1_x}" y="{TITLE_H + 42}" font-size="11" fill="{DIM}"',
        f'font-weight="600">TOTAL CONTRIBUTIONS</text>',
        f'<text x="{col1_x}" y="{TITLE_H + 72}" font-size="36" font-weight="700"',
        f'fill="{TEXT}">{total:,}</text>',
        f'<text x="{col1_x}" y="{TITLE_H + 92}" font-size="11" fill="{MUTED}">',
        f'{rng["start"]} {ARROW} {rng["end"]}</text>',
    ])

    # Longest streak
    parts.extend([
        f'<text x="{col2_x}" y="{TITLE_H + 42}" font-size="11" fill="{DIM}"',
        f'font-weight="600">LONGEST STREAK</text>',
        f'<text x="{col2_x}" y="{TITLE_H + 62}" font-size="30" font-weight="700"',
        f'fill="{TEXT}">{esc(ls_label)}</text>',
    ])
    if ls["start"]:
        parts.append(
            f'<text x="{col2_x}" y="{TITLE_H + 82}" font-size="11" fill="{MUTED}">'
            f'{ls["start"]} {ARROW} {ls["end"]}</text>'
        )

    # Best day
    parts.extend([
        f'<text x="{col2_x}" y="{TITLE_H + 112}" font-size="11" fill="{DIM}"',
        f'font-weight="600">BEST DAY</text>',
        f'<text x="{col2_x}" y="{TITLE_H + 132}" font-size="18" font-weight="600"',
        f'fill="{GREEN}">{bd["count"]} contributions</text>',
        f'<text x="{col2_x}" y="{TITLE_H + 150}" font-size="11" fill="{MUTED}">',
        f'on {bd["date"]}</text>',
    ])

    # Footer
    parts.extend([
        f'<text x="{W - PAD}" y="{H - 10}" text-anchor="end" font-size="9"',
        f'fill="{DIM}" opacity="0.5">generated {esc(gen_label)}</text>',
        '</svg>',
    ])

    return "\n".join(parts)


if __name__ == "__main__":
    data = json.load(open(IN_PATH))
    svg = render(data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
