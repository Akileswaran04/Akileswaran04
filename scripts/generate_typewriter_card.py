#!/usr/bin/env python3
"""Generate an animated SVG typewriter-card for Akileswaran's README.

Animation sequence:
  1. Letters A → K → I type in with a blinking pipe cursor, then shoot out.
  2. Full name "AKILESWARAN" reveals with per-character flip animation.
  3. Name stays on screen large and centred as the final state.

All animations use SMIL — no JS, no CSS, works in <img> tags on GitHub README.

Output: akileswaran04-profile/typewriter-card.svg
"""

import math
import os
import random

HERE = os.path.dirname(__file__)
OUT_PATH = os.path.join(HERE, "..", "typewriter-card.svg")

# ── Dimensions ──────────────────────────────────────────────────────
W, H = 860, 260
PAD = 40
TITLEBAR_H = 30
CONTENT_Y = 132   # y-centre for the big countdown letter
NAME_Y = 128       # y-centre for the final name

# ── Colors (bioluminescent teal terminal palette) ───────────────────
BG      = "#0d1117"
FRAME   = "#2dd4bf"
MUTED   = "#5eead4"
TEXT    = "#e6edf3"
LETTER  = "#2dd4bf"     # countdown letter colour
PIPE    = "#5eead4"     # pipe cursor colour
SHARD   = "#5eead4"     # shard fragment colour
NAME    = "#2dd4bf"     # final name colour
GOLD    = "#fbbf24"

DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]

# ── Timing (seconds) ────────────────────────────────────────────────
TYPE_DUR    = 0.5    # letter types in
HOLD_DUR    = 0.7    # letter holds while pipe blinks
EXPLODE_DUR = 1.0    # letter shards fly outward
CLEAN_DUR   = 0.3    # pipe fades before next cycle
CYCLE_DUR   = TYPE_DUR + HOLD_DUR + EXPLODE_DUR + CLEAN_DUR  # 2.5s

N_SHARDS = 10
random.seed(42)


def cycle_start(idx):
    """Start time (seconds) for countdown letter idx (0=A, 1=K, 2=I)."""
    return idx * CYCLE_DUR


def letter_shoot_angle():
    """Bias shard direction rightward/upward (shoots out of the pipe)."""
    angle = random.uniform(-30, 120)
    return angle


# ── Card framing ────────────────────────────────────────────────────

def make_title_bar():
    dots = "".join(
        f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{c}"/>'
        for i, c in enumerate(DOT_COLORS)
    )
    return (
        f'<rect x="0" y="0" width="{W}" height="{TITLEBAR_H}" rx="12" fill="#1f2937"/>'
        f'<rect x="0" y="{TITLEBAR_H - 8}" width="{W}" height="8" fill="#1f2937"/>'
        f'{dots}'
        f'<text x="{W/2}" y="{TITLEBAR_H/2+4}" fill="{MUTED}" font-size="12"'
        f' text-anchor="middle" font-family="\'Courier New\',monospace" font-weight="500">'
        f'        Akileswaran@github: ~/typewriter</text>'
    )


# ── Countdown letter: A, K, I ──────────────────────────────────────

def make_letter_shards(letter, start_time):
    """Return SVG for explosion shards of *letter* biased outward-upward."""
    cx = W / 2 - 18   # letter's x position
    cy = CONTENT_Y

    parts = []
    for _ in range(N_SHARDS):
        angle = letter_shoot_angle()
        dist = random.uniform(60, 150)
        dx = dist * math.cos(math.radians(angle))
        dy = dist * math.sin(math.radians(angle)) - 20  # extra upward bias
        rot = random.uniform(180, 540) * (1 if random.random() < 0.5 else -1)
        delay = random.uniform(0, 0.15)
        t0 = start_time + delay

        parts.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.12;1"'
            f' begin="{t0:.3f}s" dur="{EXPLODE_DUR:.2f}s" fill="freeze"/>'
            f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central"'
            f' font-family="\'Courier New\',monospace" font-size="72" font-weight="bold" fill="{SHARD}">{letter}'
            f'<animateTransform attributeName="transform" type="translate"'
            f' from="0,0" to="{dx:.0f},{dy:.0f}"'
            f' begin="{t0:.3f}s" dur="{EXPLODE_DUR:.2f}s" fill="freeze" additive="sum"/>'
            f'<animateTransform attributeName="transform" type="scale"'
            f' from="1" to="1.8"'
            f' begin="{t0:.3f}s" dur="{EXPLODE_DUR:.2f}s" fill="freeze" additive="sum"/>'
            f'<animateTransform attributeName="transform" type="rotate"'
            f' from="0" to="{rot:.0f}"'
            f' begin="{t0:.3f}s" dur="{EXPLODE_DUR:.2f}s" fill="freeze" additive="sum"/>'
            f'</text></g>'
        )
    return "\n".join(parts)


def make_letter_cycle(letter, idx):
    """Full cycle for one countdown letter: type in → pipe blinks → explode."""
    start = cycle_start(idx)
    total = CYCLE_DUR
    t_type = TYPE_DUR / total          # ~0.20
    t_blink_start = t_type             # 0.20
    t_blink_end = (TYPE_DUR + HOLD_DUR) / total   # ~0.48
    t_explode = t_blink_end            # 0.48

    cx = W / 2 - 18
    px = W / 2 + 18   # pipe x position
    cy = CONTENT_Y

    # Pipe blink: 3 quick blinks during hold phase, then stays solid during
    # explode, then fades quickly at the very end.
    # kt indices:  0   1    2    3    4    5    6    7    8    9    10   11   12
    pipe_kf = "0;1;1;0;1;0;1;0;1;1;1;0"
    fade_start = (TYPE_DUR + HOLD_DUR + EXPLODE_DUR) / total  # ~0.88
    fade_mid   = fade_start + 0.04 / total                     # ~0.90
    pipe_kt = (
        f"0;{0.02/total:.4f};{t_type:.4f};"
        f"{(TYPE_DUR+0.08)/total:.4f};{(TYPE_DUR+0.16)/total:.4f};"
        f"{(TYPE_DUR+0.25)/total:.4f};{(TYPE_DUR+0.35)/total:.4f};"
        f"{(TYPE_DUR+0.45)/total:.4f};{t_blink_end:.4f};"
        f"{fade_start:.4f};{fade_mid:.4f};1"
    )

    return (
        # Letter: types in → holds → explodes
        f'<g>'
        f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central"'
        f' font-family="\'Courier New\',monospace" font-size="72" font-weight="bold" fill="{LETTER}">{letter}'
        f'<animate attributeName="opacity"'
        f' values="0;1;1;0" keyTimes="0;{t_type:.4f};{t_blink_end:.4f};1"'
        f' begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="scale"'
        f' values="0;1;1;1.2" keyTimes="0;{t_type:.4f};{t_blink_end:.4f};1"'
        f' begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>'
        f'</text>'
        # Pipe cursor: types in → blinks → stays during explode → fades
        f'<text x="{px}" y="{cy}" text-anchor="middle" dominant-baseline="central"'
        f' font-family="\'Courier New\',monospace" font-size="72" font-weight="bold" fill="{PIPE}">|'
        f'<animate attributeName="opacity" values="{pipe_kf}" keyTimes="{pipe_kt}"'
        f' begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>'
        f'</text>'
        # Shards
        f'{make_letter_shards(letter, start + TYPE_DUR + HOLD_DUR)}'
        f'</g>'
    )


# ── Name reveal: A K I L E S W A R A N (slot-machine scroll) ─────

def get_char_seq(idx, target):
    """Return list of characters for scrolling animation.
    Even idx: start from 'A' and scroll up to target.
    Odd idx:  start from 'Z' and scroll down to target.
    """
    if idx % 2 == 0:
        return [chr(c) for c in range(ord("A"), ord(target) + 1)]
    else:
        return [chr(c) for c in range(ord("Z"), ord(target) - 1, -1)]


def make_name_reveal():
    """Reveal AKILESWARAN with a slot-machine scroll per character.

    Each character cycles through letters (A→target or Z→target,
    alternating per index) inside a clip-rect window, then stays.
    """
    name = "AKILESWARAN"
    n = len(name)
    stagger = 0.12     # seconds between each character's scroll start
    scroll_dur = 0.5   # duration of each character's scroll
    start = cycle_start(2) + CYCLE_DUR + 0.3  # ~7.8s after I finishes

    FONT_SIZE = 38
    CHAR_W = FONT_SIZE * 0.62
    GAP = 4               # vertical gap between stacked characters
    STEP = FONT_SIZE + GAP  # spacing between each character in the stack
    total_w = n * CHAR_W
    x0 = (W - total_w) / 2

    parts = []
    defs = []

    for i, target in enumerate(name):
        cx = x0 + i * CHAR_W + CHAR_W / 2
        seq = get_char_seq(i, target)
        ch_start = start + i * stagger

        # Clip window — shows exactly one character height
        clip_id = f"name-clip-{i}"
        clip_x = cx - CHAR_W / 2 - 2
        clip_y = NAME_Y - STEP / 2
        clip_w = CHAR_W + 4
        clip_h = STEP
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{clip_x:.1f}" y="{clip_y:.1f}" width="{clip_w:.1f}" height="{clip_h:.1f}" rx="2"/>'
            f'</clipPath>'
        )

        # If only one char (start == target), just show it directly
        if len(seq) == 1:
            parts.append(
                f'<text x="{cx:.1f}" y="{NAME_Y}" text-anchor="middle" dominant-baseline="central"'
                f' font-family="\'Courier New\',monospace" font-size="{FONT_SIZE}" font-weight="bold" fill="{NAME}">'
                f'{target}'
                f'<animate attributeName="opacity" values="0;1" keyTimes="0;0.1"'
                f' begin="{ch_start:.3f}s" dur="0.2s" fill="freeze"/>'
                f'</text>'
            )
            continue

        # Stack characters vertically (first at top, last at bottom)
        scroll_dist = (len(seq) - 1) * STEP
        stack = ""
        for ci, ch in enumerate(seq):
            y_pos = NAME_Y + ci * STEP
            stack += (
                f'<text x="{cx:.1f}" y="{y_pos:.1f}" text-anchor="middle" dominant-baseline="central"'
                f' font-family="\'Courier New\',monospace" font-size="{FONT_SIZE}" font-weight="bold"'
                f' fill="{NAME}">{ch}</text>'
            )

        # Two groups: outer has fixed clip-path, inner scrolls the stack
        parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;1" keyTimes="0;0.06"'
            f' begin="{ch_start:.3f}s" dur="{scroll_dur:.2f}s" fill="freeze"/>'
            f'{stack}'
            f'<animateTransform attributeName="transform" type="translate"'
            f' from="0,0" to="0,-{scroll_dist:.1f}"'
            f' begin="{ch_start:.3f}s" dur="{scroll_dur:.2f}s" fill="freeze"'
            f' calcMode="spline" keySplines="0.4 0 0.2 1" keyTimes="0;1"/>'
            f'</g>'
            f'</g>'
        )

    # Subtle glow after all chars have landed
    glow_start = start + n * stagger
    parts.append(
        f'<ellipse cx="{W/2}" cy="{NAME_Y}" rx="340" ry="40"'
        f' fill="none" stroke="{NAME}" stroke-width="1" opacity="0">'
        f'<animate attributeName="opacity" values="0;0.12;0.06;0.10;0.04;0.08;0"'
        f' keyTimes="0;0.1;0.3;0.5;0.7;0.85;1"'
        f' begin="{glow_start:.3f}s" dur="6s" repeatCount="indefinite"/>'
        f'</ellipse>'
    )

    return "<defs>\n" + "\n".join(defs) + "\n</defs>\n" + "\n".join(parts)


# ── Render ──────────────────────────────────────────────────────────

def render():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"',
        f'     viewBox="0 0 {W} {H}"',
        f'     font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        # Card background
        f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14"'
        f' fill="none" stroke="{FRAME}" stroke-width="1" stroke-opacity="0.55"/>',
        make_title_bar(),
        # Countdown: A → K → I
        make_letter_cycle("A", 0),
        make_letter_cycle("K", 1),
        make_letter_cycle("I", 2),
        # Name reveal
        make_name_reveal(),
        # Bottom text
        f'<text x="{W/2}" y="{H-16}" text-anchor="middle" fill="{MUTED}"',
        f' font-size="11" opacity="0.45">typewriter card — Akileswaran</text>',
        '</svg>',
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    svg = render()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
