#!/usr/bin/env python3
"""Generate terminal-window card SVGs matching contrib-heatmap's style.

Each panel replicates the heatmap's solid Cyber Cyan terminal look:
  - Gradient bg (#0d1117 -> #0f172a)
  - Cyan (#22D3EE) border, dots, and separators
  - Same card structure as info-card.svg (title bar, padding, fonts)

Call without arguments to regenerate all panels.
"""

import html
import os

# ═══════════════════════════════════════════════════════════════════
#  THEME
# ═══════════════════════════════════════════════════════════════════

BG    = "#0d1117"
BG2   = "#0f172a"
ACCENT = "#22D3EE"
MUTED  = "#38BDF8"
INK    = "#e6edf3"
DIM    = "#7d8590"

# ── Card structure (matching info-card.svg) ──────────────────────
W       = 860          # panel width
TITLE_H = 30           # title bar height
PAD     = 20           # internal padding (matches info-card KEY_X)
R       = 12           # corner radius (matches info-card)
LINE_H  = 24           # line height (increased for breathing room)
KEY_X   = PAD
EXTRA   = 22           # extra bottom padding for breathing room

# ── Title bar dot colour (matching contrib-heatmap) ───────────────
DOT = ACCENT  # solid cyan #22D3EE

HERE = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

def esc(s):
    return html.escape(s)


def card_defs():
    return f"""\
  <defs>
    <linearGradient id="card-bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG2}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
    <filter id="card-shadow" x="-5%" y="-5%" width="110%" height="125%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.35"/>
    </filter>
  </defs>"""


def card_bg(h):
    """Return the terminal-window background (matching contrib-heatmap)."""
    return f"""\
  <!-- Gradient background (matching contrib-heatmap) -->
  <rect width="{W}" height="{h}" rx="{R}" fill="url(#card-bg)" filter="url(#card-shadow)"/>
  <!-- Cyan border (matching contrib-heatmap) -->
  <rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="{R}" fill="none" stroke="{ACCENT}" stroke-width="1" stroke-opacity="0.55"/>"""


def title_bar(h, cmd):
    """Title bar — cyan dots + separator line + centred command label."""
    cy = TITLE_H / 2
    return f"""\
  <line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{ACCENT}" stroke-opacity="0.35"/>
  <circle cx="{PAD}" cy="{cy:.1f}" r="5" fill="{DOT}"/>
  <circle cx="{PAD+16}" cy="{cy:.1f}" r="5" fill="{DOT}"/>
  <circle cx="{PAD+32}" cy="{cy:.1f}" r="5" fill="{DOT}"/>
  <text x="{W/2}" y="{cy+4:.1f}" fill="{MUTED}" font-size="12" text-anchor="middle" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">akileswaran04@github: ~$ {esc(cmd)}</text>"""


def section_header(y, title):
    """'-- Title' label + thin divider rule."""
    label_w = len(title) * 8 + 24
    rule_x = KEY_X + label_w
    return (
        f'<text x="{KEY_X}" y="{y:.1f}" fill="{ACCENT}" font-size="12.5" font-weight="700">'
        f'-- {esc(title)}</text>'
        f'<line x1="{rule_x:.0f}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
        f'stroke="{ACCENT}" stroke-opacity="0.6"/>'
    )

def host_line(y, host="akileswaran04"):
    """Green@Muted:Accent hostname label + rule."""
    rule_x = KEY_X + (len(host) + 7) * 8 + 8
    return (
        f'<text x="{KEY_X}" y="{y:.1f}" font-size="14" font-weight="700">'
        f'<tspan fill="#14b8a6">{esc(host)}</tspan>'
        f'<tspan fill="{MUTED}">@</tspan>'
        f'<tspan fill="{ACCENT}">github</tspan></text>'
        f'<line x1="{rule_x:.0f}" y1="{y-4:.1f}" x2="{W-PAD}" y2="{y-4:.1f}" '
        f'stroke="{ACCENT}" stroke-opacity="0.6"/>'
    )


# ═══════════════════════════════════════════════════════════════════
#  PANEL 1 —  PROJECTS
# ═══════════════════════════════════════════════════════════════════

PROJECTS = [
    ("01", "ODYSSEY",        "LLM · EBM · LangChain",                f'<tspan fill="{MUTED}">○ processing</tspan>', None),
    ("02", "SENTRI ▸",       "Streamlit · FastAPI · XGBoost",        f'<tspan fill="{ACCENT}">● live</tspan>', "https://sentri-final.streamlit.app"),
    ("03", "Gridlock",       "LightGBM · XGBoost · Hackathon",       f'<tspan fill="{MUTED}">○ archive</tspan>', None),
    ("04", "Riddle Rush ▸",  "React · Three.js · Supabase",          f'<tspan fill="{ACCENT}">● live</tspan>', "https://csau.vercel.app"),
    ("05", "DayLog",         "React · Node.js · Firebase",           f'<tspan fill="#34D399">✓ done</tspan>', None),
]

def render_projects():
    rows_data = [("host",), ("section", "Projects")]
    for p in PROJECTS:
        rows_data.append(("proj", p))

    n_rows = len(rows_data)
    h = TITLE_H + LINE_H * n_rows + PAD + EXTRA

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(card_defs())
    parts.append(card_bg(h))
    parts.append(title_bar(h, "cat /proc/projects"))

    col_w = [40, 140, 380, 140]
    col_x = [KEY_X]
    for cw in col_w[:-1]:
        col_x.append(col_x[-1] + cw)

    y = TITLE_H + 30
    for row in rows_data:
        kind = row[0]
        if kind == "host":
            parts.append("  " + host_line(y))
        elif kind == "section":
            parts.append("  " + section_header(y, row[1]))
        elif kind == "proj":
            pid, name, stack, status, url = row[1]
            parts.append(f'  <text x="{col_x[0]}" y="{y:.1f}" fill="{DIM}" font-size="12.5">{pid}</text>')
            if url:
                parts.append(f'  <a href="{url}" target="_blank">'
                             f'<text x="{col_x[1]}" y="{y:.1f}" fill="{ACCENT}" font-size="12.5" font-weight="600">'
                             f'{esc(name)}</text></a>')
            else:
                parts.append(f'  <text x="{col_x[1]}" y="{y:.1f}" fill="{INK}" font-size="12.5" font-weight="600">{esc(name)}</text>')
            parts.append(f'  <text x="{col_x[2]}" y="{y:.1f}" fill="{INK}" font-size="12.5">{esc(stack)}</text>')
            parts.append(f'  <text x="{col_x[3]}" y="{y:.1f}" font-size="12.5">{status}</text>')
        y += LINE_H

    parts.append("</svg>")
    return "projects", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 2 —  STACK  (table format like projects/building)
# ═══════════════════════════════════════════════════════════════════

STACK_ROWS = [
    ("Languages", "C++, Python, JavaScript"),
    ("Frontend",  "React, Three.js"),
    ("Backend",   "Node.js, FastAPI, Streamlit"),
    ("Database",  "PostgreSQL, Firebase"),
    ("ML/AI",     "XGBoost, TensorFlow, PyTorch, scikit-learn"),
    ("Tools",     "Git, Docker"),
]


def render_stack():
    rows_data = [("host",), ("section", "Stack")]
    for cat, skills in STACK_ROWS:
        rows_data.append(("skill_row", cat, skills))
    n_rows = len(rows_data)
    h = TITLE_H + LINE_H * n_rows + PAD + EXTRA

    col_w = [130, 660]
    col_x = [KEY_X, KEY_X + col_w[0]]

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(card_defs())
    parts.append(card_bg(h))
    parts.append(title_bar(h, "skills"))

    y = TITLE_H + 30
    for row in rows_data:
        kind = row[0]
        if kind == "host":
            parts.append("  " + host_line(y))
        elif kind == "section":
            parts.append("  " + section_header(y, row[1]))
        elif kind == "skill_row":
            cat, skills = row[1], row[2]
            parts.append(f'  <text x="{col_x[0]}" y="{y:.1f}" fill="{ACCENT}" font-size="12.5" font-weight="700">{esc(cat)}</text>')
            parts.append(f'  <text x="{col_x[1]}" y="{y:.1f}" fill="{INK}" font-size="12.5">{esc(skills)}</text>')
        y += LINE_H

    parts.append("</svg>")
    return "stack", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 3 —  BUILDING NOW
# ═══════════════════════════════════════════════════════════════════

BUILDING = [
    ("001", "SENTRI",      "Streamlit · FastAPI · XGBoost", "42%"),
    ("002", "Riddle Rush", "React · Three.js · Supabase",    "35%"),
    ("003", "ODYSSEY",     "LLM · EBM · LangChain",         "38%"),
]

def render_building():
    rows_data = [("host",), ("section", "Active Processes")]
    for b in BUILDING:
        rows_data.append(("proc", b))
    n_rows = len(rows_data)
    h = TITLE_H + LINE_H * n_rows + PAD + EXTRA

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(card_defs())
    parts.append(card_bg(h))
    parts.append(title_bar(h, "ps aux | grep building"))

    col_w = [40, 130, 420, 80]
    col_x = [KEY_X]
    for cw in col_w[:-1]:
        col_x.append(col_x[-1] + cw)

    y = TITLE_H + 30
    for row in rows_data:
        kind = row[0]
        if kind == "host":
            parts.append("  " + host_line(y))
        elif kind == "section":
            parts.append("  " + section_header(y, row[1]))
        elif kind == "proc":
            pid, name, stack, cpu = row[1]
            parts.append(f'  <text x="{col_x[0]}" y="{y:.1f}" fill="{DIM}" font-size="12.5">{pid}</text>')
            parts.append(f'  <text x="{col_x[1]}" y="{y:.1f}" fill="{INK}" font-size="12.5" font-weight="600">{esc(name)}</text>')
            parts.append(f'  <text x="{col_x[2]}" y="{y:.1f}" fill="{INK}" font-size="12.5">{esc(stack)}</text>')
            parts.append(f'  <text x="{col_x[3]}" y="{y:.1f}" fill="{ACCENT}" font-size="12.5" font-weight="600">{cpu}</text>')
        y += LINE_H

    parts.append("</svg>")
    return "building", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 4 —  TAGLINE
# ═══════════════════════════════════════════════════════════════════

def render_tagline():
    lines = [
        'Full-Stack Developer | Applied ML',
        'Full-Stack x AI/ML — turning data into decisions',
    ]
    n_rows = 3  # host + 2 text lines
    h = TITLE_H + LINE_H * n_rows + PAD + EXTRA

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(card_defs())
    parts.append(card_bg(h))
    parts.append(title_bar(h, 'echo $TAGLINE'))

    y = TITLE_H + 30
    parts.append("  " + host_line(y))
    y += LINE_H

    for i, line in enumerate(lines):
        colour = ACCENT if i == 0 else INK
        sz = 16 if i == 0 else 14
        parts.append(f'  <text x="{W/2}" y="{y:.1f}" fill="{colour}" font-size="{sz}" text-anchor="middle" font-weight="500">{esc(line)}</text>')
        y += LINE_H

    parts.append("</svg>")
    return "tagline", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    panels = [
        render_projects(),
        render_stack(),
        render_building(),
        render_tagline(),
    ]
    for name, svg in panels:
        path = os.path.join(HERE, "..", f"glass-{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"wrote {path} ({len(svg)} bytes)")
    print("done — all glass panels generated")
