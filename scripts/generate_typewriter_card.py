#!/usr/bin/env python3
"""Generate an animated SVG typewriter-card for a GitHub profile README.

Animation sequence:
  1. Countdown letters (e.g. A → K → I) type in with a blinking pipe
     cursor, then shoot out as shards.
  2. Full name (e.g. "AKILESWARAN") reveals with a slot-machine scroll
     per character (each cycles from 'A' or 'Z' alternating).
  3. Name stays on screen with glowing underscores that pulse in a
     left-to-right wave.

All animations use SMIL — no JS, no CSS, works in <img> tags on
GitHub README.  Fully parameterised — change the constants at the top
of this file to swap names, colours, or timings.

Output: akileswaran04-profile/typewriter-card.svg
"""

import math
import os
import random
import sys
import xml.etree.ElementTree as ET

# ═══════════════════════════════════════════════════════════════════
# CONFIG — edit these to re-theme / re-target the card
# ═══════════════════════════════════════════════════════════════════

CONFIG = {
    # ── Content ────────────────────────────────────────────────
    "USERNAME":         "Akileswaran04",
    "COUNTDOWN_LETTERS": [],
    "FULL_NAME":        "AKILESWARAN",

    # ── Dimensions ─────────────────────────────────────────────
    "PAD":              40,
    "TITLEBAR_H":       30,
    "H":                130,             # card height
    "FONT_SIZE":        38,              # name font size
    "NAME_GAP":         4,               # vertical gap between stacked scroll chars

    # ── Countdown-letter timing (seconds) ──────────────────────
    "TYPE_DUR":         0.5,
    "HOLD_DUR":         0.7,
    "EXPLODE_DUR":      1.0,
    "CLEAN_DUR":        0.3,

    # ── Name-reveal timing ─────────────────────────────────────
    "STAGGER":          0.12,            # seconds between each char's scroll start
    "BASE_SCROLL":       0.15,           # base scroll duration
    "PER_STEP":          0.018,          # additional seconds per scroll step

    # ── Underscore wave ────────────────────────────────────────
    "WAVE_STAGGER":      0.08,           # seconds between consecutive underscores
    "WAVE_GAP":          0.5,            # gap after last underscore lands before wave

    # ── Shards ─────────────────────────────────────────────────
    "N_SHARDS":          10,
    "SHARD_MIN_DIST":    60,
    "SHARD_MAX_DIST":    150,

    # ── Colors (bioluminescent teal terminal palette) ──────────
    "BG":               "#0d1117",
    "FRAME":            "#2dd4bf",
    "MUTED":            "#5eead4",
    "LETTER":           "#2dd4bf",       # countdown letter
    "PIPE":             "#5eead4",       # pipe cursor
    "SHARD":            "#5eead4",       # explosion fragments
    "NAME":             "#2dd4bf",       # final name
    "DOT_COLORS":       ["#ff5f56", "#ffbd2e", "#27c93f"],
    "TITLE_BG":         "#1f2937",
}


# ═══════════════════════════════════════════════════════════════════
# Derived constants (computed, not user-editable)
# ═══════════════════════════════════════════════════════════════════

def _derive(c):
    """Compute derived values from CONFIG."""
    c = c.copy()
    c["CYCLE_DUR"] = c["TYPE_DUR"] + c["HOLD_DUR"] + c["EXPLODE_DUR"] + c["CLEAN_DUR"]
    c["CHAR_W"] = c["FONT_SIZE"] * 0.62
    c["STEP"] = c["FONT_SIZE"] + c["NAME_GAP"]
    # Minimum card width: name + left/right margins + shard room
    min_w = 2 * c["PAD"] + len(c["FULL_NAME"]) * c["CHAR_W"] + 80
    c["W"] = max(860, int(math.ceil(min_w)))
    c["Y_CENTER"] = c["H"] / 2 - 5          # vertical centre for both countdown & name
    return c


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

random.seed(42)

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "typewriter-card.svg")


def _validate(c):
    """Raise on invalid config."""
    name = c["FULL_NAME"]
    if not name:
        raise ValueError("FULL_NAME must not be empty")
    cleaned = "".join(ch for ch in name.upper() if ch.isalpha())
    if cleaned != name.upper():
        raise ValueError(
            f"FULL_NAME contains non-A-Z characters: {name!r}. "
            f"Use only letters A-Z (spaces, digits, symbols are not supported)."
        )
    for ch in c["COUNTDOWN_LETTERS"]:
        if not ch.isalpha() or ch.upper() != ch:
            raise ValueError(
                f"COUNTDOWN_LETTERS entries must be uppercase A-Z, got {ch!r}"
            )


def cycle_start(idx, c):
    """Start time (seconds) for countdown letter idx."""
    return idx * c["CYCLE_DUR"]


def get_char_seq(idx, target):
    """Return list of characters for scrolling animation.

    Even idx: start from 'A' and scroll up to target.
    Odd idx:  start from 'Z' and scroll down to target.

    If start == target, returns a single-element list (fast path).
    """
    if idx % 2 == 0:
        return [chr(c) for c in range(ord("A"), ord(target) + 1)]
    else:
        return [chr(c) for c in range(ord("Z"), ord(target) - 1, -1)]


# ═══════════════════════════════════════════════════════════════════
# SVG builders
# ═══════════════════════════════════════════════════════════════════

def make_title_bar(c):
    dots = "".join(
        f'<circle cx="{c["PAD"] + i * 16}" cy="{c["TITLEBAR_H"] / 2}" '
        f'r="5" fill="{col}"/>'
        for i, col in enumerate(c["DOT_COLORS"])
    )
    title = f'{c["USERNAME"]}@github: ~/typewriter'
    return (
        f'<rect x="0" y="0" width="{c["W"]}" height="{c["TITLEBAR_H"]}" '
        f'rx="12" fill="{c["TITLE_BG"]}"/>'
        f'<rect x="0" y="{c["TITLEBAR_H"] - 8}" width="{c["W"]}" '
        f'height="8" fill="{c["TITLE_BG"]}"/>'
        f'{dots}'
        f'<text x="{c["W"] / 2}" y="{c["TITLEBAR_H"] / 2 + 4}" '
        f'fill="{c["MUTED"]}" font-size="12" text-anchor="middle" '
        f'font-family="\'Courier New\',monospace" font-weight="500">'
        f'{title}</text>'
    )


def make_shard(letter, start_time, c):
    """Return SVG for one explosion shard of *letter* at *start_time*."""
    angle = random.uniform(-10, 100)        # rightward / upward
    dist = random.uniform(c["SHARD_MIN_DIST"], c["SHARD_MAX_DIST"])
    dx = dist * math.cos(math.radians(angle))
    dy = dist * math.sin(math.radians(angle)) - 20   # extra upward bias
    rot = random.uniform(180, 540) * (1 if random.random() < 0.5 else -1)
    delay = random.uniform(0, 0.15)
    t0 = start_time + delay
    cx = c["W"] / 2 - 18
    cy = c["Y_CENTER"]

    return (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" values="1;1;0" '
        f'keyTimes="0;0.12;1" begin="{t0:.3f}s" '
        f'dur="{c["EXPLODE_DUR"]:.2f}s" fill="freeze"/>'
        f'<text x="{cx}" y="{cy}" text-anchor="middle" '
        f'dominant-baseline="central" '
        f'font-family="\'Courier New\',monospace" font-size="72" '
        f'font-weight="bold" fill="{c["SHARD"]}">{letter}'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0,0" to="{dx:.0f},{dy:.0f}" '
        f'begin="{t0:.3f}s" dur="{c["EXPLODE_DUR"]:.2f}s" '
        f'fill="freeze" additive="sum"/>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'from="1" to="1.8" '
        f'begin="{t0:.3f}s" dur="{c["EXPLODE_DUR"]:.2f}s" '
        f'fill="freeze" additive="sum"/>'
        f'<animateTransform attributeName="transform" type="rotate" '
        f'from="0" to="{rot:.0f}" '
        f'begin="{t0:.3f}s" dur="{c["EXPLODE_DUR"]:.2f}s" '
        f'fill="freeze" additive="sum"/>'
        f'</text></g>'
    )


def make_letter_cycle(letter, idx, c):
    """Full cycle: letter types in → pipe blinks → explodes."""
    start = cycle_start(idx, c)
    total = c["CYCLE_DUR"]
    t_type = c["TYPE_DUR"] / total
    t_blink_end = (c["TYPE_DUR"] + c["HOLD_DUR"]) / total

    cx = c["W"] / 2 - 18
    px = c["W"] / 2 + 18          # pipe position
    cy = c["Y_CENTER"]

    # Pipe: 3 blinks, solid during explode, quick fade
    pipe_kf = "0;1;1;0;1;0;1;0;1;1;1;0"
    fade_start = (c["TYPE_DUR"] + c["HOLD_DUR"] + c["EXPLODE_DUR"]) / total
    fade_mid = fade_start + 0.04 / total
    pipe_kt = (
        f"0;{0.02/total:.4f};{t_type:.4f};"
        f"{(c['TYPE_DUR']+0.08)/total:.4f};{(c['TYPE_DUR']+0.16)/total:.4f};"
        f"{(c['TYPE_DUR']+0.25)/total:.4f};{(c['TYPE_DUR']+0.35)/total:.4f};"
        f"{(c['TYPE_DUR']+0.45)/total:.4f};{t_blink_end:.4f};"
        f"{fade_start:.4f};{fade_mid:.4f};1"
    )

    return (
        f'<g>'
        # Letter
        f'<text x="{cx}" y="{cy}" text-anchor="middle" '
        f'dominant-baseline="central" '
        f'font-family="\'Courier New\',monospace" font-size="72" '
        f'font-weight="bold" fill="{c["LETTER"]}">{letter}'
        f'<animate attributeName="opacity" '
        f'values="0;1;1;0" keyTimes="0;{t_type:.4f};{t_blink_end:.4f};1" '
        f'begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="scale" '
        f'values="0;1;1;1.2" keyTimes="0;{t_type:.4f};{t_blink_end:.4f};1" '
        f'begin="{start:.3f}s" dur="{total:.2f}s" fill="freeze"/>'
        f'</text>'
        # Pipe cursor
        f'<text x="{px}" y="{cy}" text-anchor="middle" '
        f'dominant-baseline="central" '
        f'font-family="\'Courier New\',monospace" font-size="72" '
        f'font-weight="bold" fill="{c["PIPE"]}">|'
        f'<animate attributeName="opacity" values="{pipe_kf}" '
        f'keyTimes="{pipe_kt}" begin="{start:.3f}s" '
        f'dur="{total:.2f}s" fill="freeze"/>'
        f'</text>'
        # Shards
        f'{"".join(make_shard(letter, start + c["TYPE_DUR"] + c["HOLD_DUR"], c) for _ in range(c["N_SHARDS"]))}'
        f'</g>'
    )


def make_name_reveal(c):
    """Slot-machine scroll for each character of FULL_NAME."""
    name = c["FULL_NAME"]
    n = len(name)
    stagger = c["STAGGER"]
    base_scroll = c["BASE_SCROLL"]
    per_step = c["PER_STEP"]
    wave_stagger = c["WAVE_STAGGER"]
    wave_gap = c["WAVE_GAP"]

    n_countdown = len(c["COUNTDOWN_LETTERS"])
    reveal_start = n_countdown * c["CYCLE_DUR"] + 0.3  # after last countdown

    parts = []
    defs = []

    # Glow filter
    defs.append(
        '<filter id="underscore-glow">'
        '<feGaussianBlur stdDeviation="2" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/>'
        '<feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
    )

    # Pre-compute scroll durations for wave_start
    char_data = []  # (cx, seq, scroll_dur, underscore_land)
    for i, target in enumerate(name):
        cx = (c["W"] - n * c["CHAR_W"]) / 2 + i * c["CHAR_W"] + c["CHAR_W"] / 2
        seq = get_char_seq(i, target)
        scroll_dur = base_scroll + per_step * max(0, len(seq) - 1)
        ch_start = reveal_start + i * stagger
        underscore_land = ch_start + scroll_dur
        char_data.append((cx, seq, scroll_dur, underscore_land, ch_start))

    last_land = max(d[3] for d in char_data) if char_data else 0
    wave_start = last_land + 0.6 + wave_gap  # after last landing animate + gap

    for i, (target, (cx, seq, scroll_dur, underscore_land, ch_start)) in enumerate(
        zip(name, char_data)
    ):
        # Clip window
        clip_id = f"name-clip-{i}"
        clip_x = cx - c["CHAR_W"] / 2 - 2
        clip_y = c["Y_CENTER"] - c["STEP"] / 2
        defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="{clip_x:.1f}" y="{clip_y:.1f}" '
            f'width="{c["CHAR_W"] + 4:.1f}" height="{c["STEP"]:.1f}" rx="2"/>'
            f'</clipPath>'
        )

        wave_begin = wave_start + i * wave_stagger
        underscore_y = c["Y_CENTER"] + c["FONT_SIZE"] / 2 + 4

        if len(seq) == 1:
            # Single character (start == target) — just fade in
            parts.append(
                f'<text x="{cx:.1f}" y="{c["Y_CENTER"]}" '
                f'text-anchor="middle" dominant-baseline="central" '
                f'font-family="\'Courier New\',monospace" '
                f'font-size="{c["FONT_SIZE"]}" font-weight="bold" '
                f'fill="{c["NAME"]}">{target}'
                f'<animate attributeName="opacity" values="0;1" '
                f'keyTimes="0;0.1" begin="{ch_start:.3f}s" '
                f'dur="0.2s" fill="freeze"/>'
                f'</text>'
                f'<rect x="{cx - c["CHAR_W"] / 2:.1f}" '
                f'y="{underscore_y:.1f}" '
                f'width="{c["CHAR_W"]:.1f}" height="2" rx="1" '
                f'fill="{c["NAME"]}" filter="url(#underscore-glow)" '
                f'opacity="0">'
                f'<animate attributeName="opacity" '
                f'values="0;0;0.8;0.4;0.9" '
                f'keyTimes="0;0.2;0.35;0.65;1" '
                f'begin="{ch_start:.3f}s" dur="0.6s" fill="freeze"/>'
                f'<animate attributeName="opacity" '
                f'values="0.9;0.2;0.9" keyTimes="0;0.5;1" '
                f'dur="0.8s" begin="{wave_begin:.3f}s" '
                f'repeatCount="indefinite"/>'
                f'</rect>'
            )
            continue

        # Multi-character scroll stack
        scroll_dist = (len(seq) - 1) * c["STEP"]
        stack = ""
        for ci, ch in enumerate(seq):
            yp = c["Y_CENTER"] + ci * c["STEP"]
            stack += (
                f'<text x="{cx:.1f}" y="{yp:.1f}" '
                f'text-anchor="middle" dominant-baseline="central" '
                f'font-family="\'Courier New\',monospace" '
                f'font-size="{c["FONT_SIZE"]}" font-weight="bold" '
                f'fill="{c["NAME"]}">{ch}</text>'
            )

        parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;1" '
            f'keyTimes="0;0.06" begin="{ch_start:.3f}s" '
            f'dur="{scroll_dur:.2f}s" fill="freeze"/>'
            f'{stack}'
            f'<animateTransform attributeName="transform" '
            f'type="translate" from="0,0" to="0,-{scroll_dist:.1f}" '
            f'begin="{ch_start:.3f}s" dur="{scroll_dur:.2f}s" '
            f'fill="freeze" calcMode="spline" '
            f'keySplines="0.4 0 0.2 1" keyTimes="0;1"/>'
            f'</g>'
            f'</g>'
            f'<rect x="{cx - c["CHAR_W"] / 2:.1f}" '
            f'y="{underscore_y:.1f}" '
            f'width="{c["CHAR_W"]:.1f}" height="2" rx="1" '
            f'fill="{c["NAME"]}" filter="url(#underscore-glow)" '
            f'opacity="0">'
            f'<animate attributeName="opacity" '
            f'values="0;0;0.8;0.4;0.9" '
            f'keyTimes="0;0.2;0.35;0.65;1" '
            f'begin="{underscore_land:.3f}s" dur="0.6s" fill="freeze"/>'
            f'<animate attributeName="opacity" '
            f'values="0.9;0.2;0.9" keyTimes="0;0.5;1" '
            f'dur="0.8s" begin="{wave_begin:.3f}s" '
            f'repeatCount="indefinite"/>'
            f'</rect>'
        )

    # Glow ellipse after all characters reveal
    glow_start = reveal_start + n * stagger
    parts.append(
        f'<ellipse cx="{c["W"] / 2}" cy="{c["Y_CENTER"]}" '
        f'rx="{c["W"] * 0.4:.0f}" ry="40" '
        f'fill="none" stroke="{c["NAME"]}" stroke-width="1" opacity="0">'
        f'<animate attributeName="opacity" '
        f'values="0;0.12;0.06;0.10;0.04;0.08;0" '
        f'keyTimes="0;0.1;0.3;0.5;0.7;0.85;1" '
        f'begin="{glow_start:.3f}s" dur="6s" repeatCount="indefinite"/>'
        f'</ellipse>'
    )

    return "<defs>\n" + "\n".join(defs) + "\n</defs>\n" + "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
# Render
# ═══════════════════════════════════════════════════════════════════

def render(cfg):
    """Build the complete SVG document string."""
    c = _derive(cfg)
    _validate(c)

    cd = c["COUNTDOWN_LETTERS"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{c["W"]}" height="{c["H"]}" '
        f'viewBox="0 0 {c["W"]} {c["H"]}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        # Background
        f'<rect width="{c["W"]}" height="{c["H"]}" rx="14" fill="{c["BG"]}"/>',
        f'<rect x="0.5" y="0.5" width="{c["W"] - 1}" height="{c["H"] - 1}" '
        f'rx="14" fill="none" stroke="{c["FRAME"]}" '
        f'stroke-width="1" stroke-opacity="0.55"/>',
        make_title_bar(c),
        # Countdown letters
        *[make_letter_cycle(ch, i, c) for i, ch in enumerate(cd)],
        # Name reveal
        make_name_reveal(c),
        # Bottom text
        f'<text x="{c["W"] / 2}" y="{c["H"] - 16}" '
        f'text-anchor="middle" fill="{c["MUTED"]}" '
        f'font-size="11" opacity="0.45">'
        f'typewriter card — {c["FULL_NAME"]}</text>',
        '</svg>',
    ]
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    svg = render(CONFIG)

    # Validate well-formed XML
    try:
        ET.fromstring(svg)
    except ET.ParseError as e:
        print(f"ERROR: SVG is not valid XML — {e}", file=sys.stderr)
        sys.exit(1)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes) — valid XML")
