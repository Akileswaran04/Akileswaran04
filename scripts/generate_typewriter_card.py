#!/usr/bin/env python3
"""Generate an animated SVG "Exploding Countdown" card.

A terminal-style card that counts down 5 → 4 → 3 → 2 → 1 → GO!
Each number types in, holds briefly, then explodes into shards
that fly outward and fade — all via SMIL animations (no JS).

Output: akileswaran04-profile/typewriter-card.svg
"""

import math
import os
import random

HERE = os.path.dirname(__file__)
OUT_PATH = os.path.join(HERE, "..", "typewriter-card.svg")

# ── Dimensions ──────────────────────────────────────────────────────
W, H = 640, 320
PAD = 40
TITLEBAR_H = 34
CONTENT_Y = 170  # y-centre for the big countdown number

# ── Colors (bioluminescent teal terminal palette) ───────────────────
BG      = "#0d1117"
CARD_BG = "#161b22"
FRAME   = "#2dd4bf"
MUTED   = "#5eead4"
TEXT    = "#e6edf3"
NUM_CLR = "#2dd4bf"     # countdown number colour
SHARD   = "#5eead4"     # shard fragment colour
FINAL   = "#2dd4bf"     # final "GO!" colour
GOLD    = "#fbbf24"     # accent

DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]

# ── Timing (seconds) ────────────────────────────────────────────────
TYPE_DUR    = 0.5   # number types in
HOLD_DUR    = 0.8   # number holds on screen
EXPLODE_DUR = 1.0   # shards fly outward
CYCLE_DUR   = TYPE_DUR + HOLD_DUR + EXPLODE_DUR + 0.3  # ~2.6s

N_SHARDS = 10  # shards per explosion
random.seed(42)


def cycle_start(n):
    """Return start time (seconds) for countdown number n (5=first)."""
    return (5 - n) * CYCLE_DUR


def make_title_bar():
    dots = "".join(
        f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>'
        for i, c in enumerate(DOT_COLORS)
    )
    return f"""
    <rect x="0" y="0" width="{W}" height="{TITLEBAR_H}" rx="12" fill="#1f2937"/>
    <rect x="0" y="{TITLEBAR_H - 10}" width="{W}" height="10" fill="#1f2937"/>
    {dots}
    <text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12"
          text-anchor="middle" font-family="'Courier New',monospace"
          font-weight="500">Akileswaran@github: ~/countdown</text>
    """


def make_shard(num, start):
    """Return SVG for one explosion shard of *num* at *start* time."""
    angle = random.uniform(0, 360)
    dist = random.uniform(70, 160)
    dx = dist * math.cos(math.radians(angle))
    dy = dist * math.sin(math.radians(angle))
    rot = random.uniform(180, 540) * (1 if random.random() < 0.5 else -1)
    delay = random.uniform(0, 0.18)

    return f"""
    <g opacity="0">
      <animate attributeName="opacity" values="1;1;0" keyTimes="0;0.15;1"
               begin="{start + delay:.3f}s" dur="{EXPLODE_DUR:.2f}s" fill="freeze"/>
      <text x="{W / 2}" y="{CONTENT_Y}" text-anchor="middle"
            dominant-baseline="central"
            font-family="'Courier New',monospace" font-size="72" font-weight="bold"
            fill="{SHARD}">{num}
        <animateTransform attributeName="transform" type="translate"
                         from="0,0" to="{dx:.0f},{dy:.0f}"
                         begin="{start + delay:.3f}s" dur="{EXPLODE_DUR:.2f}s"
                         fill="freeze" additive="sum"/>
        <animateTransform attributeName="transform" type="scale"
                         from="1" to="1.8"
                         begin="{start + delay:.3f}s" dur="{EXPLODE_DUR:.2f}s"
                         fill="freeze" additive="sum"/>
        <animateTransform attributeName="transform" type="rotate"
                         from="0" to="{rot:.0f}"
                         begin="{start + delay:.3f}s" dur="{EXPLODE_DUR:.2f}s"
                         fill="freeze" additive="sum"/>
      </text>
    </g>"""


def make_countdown_number(num):
    """Return SVG for one countdown number (types-in, holds, fades out)."""
    start = cycle_start(num)
    total = TYPE_DUR + HOLD_DUR + EXPLODE_DUR

    # Phase keyframes: 0=invisible, 1=visible, 2=explode
    t1 = TYPE_DUR / total
    t2 = (TYPE_DUR + HOLD_DUR) / total

    return f"""
    <g>
      <text x="{W / 2}" y="{CONTENT_Y}" text-anchor="middle"
            dominant-baseline="central"
            font-family="'Courier New',monospace" font-size="72" font-weight="bold"
            fill="{NUM_CLR}">{num}
        <animate attributeName="opacity"
                 values="0;1;1;0" keyTimes="0;{t1:.3f};{t2:.3f};1"
                 begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>
        <animateTransform attributeName="transform" type="scale"
                 values="0;1;1;1.3" keyTimes="0;{t1:.3f};{t2:.3f};1"
                 begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>
      </text>
      { ''.join(make_shard(num, start + TYPE_DUR + HOLD_DUR) for _ in range(N_SHARDS))}
    </g>"""


def make_final_state():
    """Return SVG for the final '→ GO!' state after countdown ends."""
    start = cycle_start(1) + CYCLE_DUR - 0.3  # ~12.7s
    return f"""
    <g>
      <text x="{W / 2}" y="{CONTENT_Y - 10}" text-anchor="middle"
            dominant-baseline="central"
            font-family="'Courier New',monospace" font-size="60" font-weight="bold"
            fill="{FINAL}">
        <!-- type in -->
        <animate attributeName="opacity" values="0;1" keyTimes="0;0.15"
                 begin="{start:.3f}s" dur="0.5s" fill="freeze"/>
        <animateTransform attributeName="transform" type="scale"
                 values="2;1" keyTimes="0;0.15"
                 begin="{start:.3f}s" dur="0.5s" fill="freeze"/>
        <!-- perpetual gentle pulse (pure SMIL) -->
        <animateTransform attributeName="transform" type="translate"
                 values="0,0;0,-3;0,0" keyTimes="0;0.5;1"
                 begin="{start + 0.5:.3f}s" dur="3s" repeatCount="indefinite"
                 additive="sum"/>
        &#8594; GO!
      </text>
      <!-- glow ring: initial pulse, then perpetual gentle breathe -->
      <circle cx="{W / 2}" cy="{CONTENT_Y - 10}" r="80" fill="none"
              stroke="{FINAL}" stroke-width="1.5" opacity="0">
        <animate attributeName="opacity" values="0;0.15;0;0.08;0.04;0.08"
                 keyTimes="0;0.08;0.25;0.5;0.75;1"
                 begin="{start + 0.5:.3f}s" dur="4s" repeatCount="indefinite"/>
        <animate attributeName="r" values="40;90;40"
                 keyTimes="0;0.5;1"
                 begin="{start + 0.5:.3f}s" dur="4s" repeatCount="indefinite"/>
      </circle>
    </g>"""


def render():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"',
        f'     viewBox="0 0 {W} {H}"',
        f'     font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        
        f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14"',
        f'      fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        make_title_bar(),
        # Countdown numbers 5 → 1
        *[make_countdown_number(n) for n in (5, 4, 3, 2, 1)],
        make_final_state(),
        # Bottom text
        f'<text x="{W / 2}" y="{H - 18}" text-anchor="middle" fill="{MUTED}"',
        f'      font-size="11" opacity="0.6">countdown v1.0 — Akileswaran</text>',
        '</svg>',
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    svg = render()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
