#!/usr/bin/env python3
"""Generate glassmorphism panel SVGs — exactly matching info-card.svg's
card structure (title bar, padding, font sizes, section headers, key/value
alignment) with a liquid-glass surface treatment applied on top.

Each panel is a standalone SVG stacked vertically in the README.
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
LINE_H  = 20.5         # line height (matches info-card)
KEY_X   = PAD
VAL_X   = PAD + 92     # value offset (matches info-card)

# ── Traffic-light dot colours (macOS chrome) ─────────────────────
DOT_R = "#ff5f56"
DOT_Y = "#ffbd2e"
DOT_G = "#27c93f"

HERE = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════

def esc(s):
    return html.escape(s)


def glass_defs():
    return f"""\
  <defs>
    <linearGradient id="g-bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG2}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
    <linearGradient id="g-top" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.18"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <filter id="g-blur-lg" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="50"/>
    </filter>
    <filter id="g-blur-sm" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="24"/>
    </filter>
  </defs>"""


def glass_bg(h):
    """Return glass surface elements — gradient bg, blobs, glass pane,
    white border, top highlight — placed BEFORE the card chrome."""
    return f"""\
  <!-- Gradient background -->
  <rect width="{W}" height="{h}" rx="{R}" fill="url(#g-bg)"/>
  <!-- Colour blobs -->
  <circle cx="{W*0.18:.0f}" cy="{h*0.35:.0f}" r="{W*0.14:.0f}" fill="{ACCENT}" opacity="0.12" filter="url(#g-blur-lg)"/>
  <circle cx="{W*0.78:.0f}" cy="{h*0.65:.0f}" r="{W*0.10:.0f}" fill="{MUTED}"  opacity="0.10" filter="url(#g-blur-lg)"/>
  <circle cx="{W*0.50:.0f}" cy="{h*0.15:.0f}" r="{W*0.07:.0f}" fill="{ACCENT}" opacity="0.08" filter="url(#g-blur-sm)"/>
  <!-- Glass pane surface (8% white) -->
  <rect x="0" y="0" width="{W}" height="{h}" rx="{R}" fill="#ffffff" fill-opacity="0.08"/>
  <!-- Glass border (18% white) -->
  <rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="{R}" fill="none" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1"/>
  <!-- Top light-catching highlight -->
  <rect x="2" y="2" width="{W-4}" height="6" rx="{R}" fill="url(#g-top)"/>"""


def title_bar(h, cmd):
    """Traffic-light dots + separator line + centred command label."""
    cy = TITLE_H / 2
    return f"""\
  <!-- Title bar chrome (solid, not glass) -->
  <line x1="0" y1="{TITLE_H}" x2="{W}" y2="{TITLE_H}" stroke="{MUTED}" stroke-opacity="0.35"/>
  <circle cx="{PAD}" cy="{cy:.1f}" r="5" fill="{DOT_R}"/>
  <circle cx="{PAD+16}" cy="{cy:.1f}" r="5" fill="{DOT_Y}"/>
  <circle cx="{PAD+32}" cy="{cy:.1f}" r="5" fill="{DOT_G}"/>
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


def kv_row(y, key, val):
    """Key (cyan) / value (white) pair."""
    return (
        f'<text x="{KEY_X}" y="{y:.1f}" fill="{ACCENT}" font-size="12.5" font-weight="700">'
        f'{esc(key)}</text>'
        f'<text x="{VAL_X}" y="{y:.1f}" fill="{INK}" font-size="12.5">{esc(val)}</text>'
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
#  PANEL 1 —  WHOAMI  (identity)
# ═══════════════════════════════════════════════════════════════════

def render_whoami():
    rows = [
        ("host",),
        ("kv", "NAME",     "Akileswaran A"),
        ("kv", "TITLE",    "Software Engineering Intern · Full-Stack & ML"),
        ("kv", "LOCATION", "CEG, Anna University · B.Tech IT"),
        ("kv-tspan", "STATUS", ACCENT, "● actively building"),
        ("kv", "FOCUS",    "Multi-agent AI systems · Full-stack · Applied ML"),
    ]
    h = TITLE_H + LINE_H * (len(rows) + 0.5) + PAD
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
    parts.append(title_bar(h, "whoami"))

    y = TITLE_H + 30
    for row in rows:
        kind = row[0]
        if kind == "host":
            parts.append("  " + host_line(y))
        elif kind == "kv":
            key, val = row[1], row[2]
            parts.append("  " + kv_row(y, key, val))
        elif kind == "kv-tspan":
            key, colour, val = row[1], row[2], row[3]
            parts.append(
                f'<text x="{KEY_X}" y="{y:.1f}" fill="{ACCENT}" font-size="12.5" font-weight="700">'
                f'{esc(key)}</text>'
                f'<text x="{VAL_X}" y="{y:.1f}" font-size="12.5">'
                f'<tspan fill="{colour}">{esc(val)}</tspan></text>'
            )
        y += LINE_H

    parts.append("</svg>")
    return "whoami", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 2 —  NETSTAT  (social links — pill badges)
# ═══════════════════════════════════════════════════════════════════

SOCIAL = [
    ("LinkedIn",  "#0A66C2", "https://linkedin.com/in/akileswaran-ammamuthu"),
    ("GitHub",    "#181717", "https://github.com/Akileswaran04"),
    ("LeetCode",  "#FFA116", "https://leetcode.com/u/Akileswaran04/", "#000000"),
    ("SENTRI",    "#FF4B4B", "https://sentri-final.streamlit.app"),
]


def pill(x, y, text, bg, tc="#ffffff"):
    tw = len(text) * 8.5 + 24
    return (
        f'<g>'
        f'<rect x="{x:.0f}" y="{y-9:.0f}" width="{tw:.0f}" height="24" rx="12" fill="{bg}"/>'
        f'<text x="{x+tw/2:.0f}" y="{y+4:.0f}" fill="{tc}" font-size="12.5" '
        f'font-weight="600" text-anchor="middle" font-family="ui-monospace,monospace">'
        f'{esc(text)}</text></g>'
    ), tw


def render_netstat():
    rows = [
        ("host",),
        ("section", "Connections"),
    ]
    # One row for pill badges
    n_rows = 3  # host + section header + badge row
    h = TITLE_H + LINE_H * n_rows + PAD + 12

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
    parts.append(title_bar(h, "netstat --connections"))

    y = TITLE_H + 30
    parts.append("  " + host_line(y))
    y += LINE_H

    # Section header
    parts.append("  " + section_header(y, "Connections"))
    y += LINE_H

    # Badges
    bx = KEY_X
    by = y + 14  # vertical centre for badges
    for s in SOCIAL:
        label, colour, url = s[0], s[1], s[2]
        tc = s[3] if len(s) > 3 else "#ffffff"
        piece, bw = pill(bx, by, label, colour, tc)
        parts.append(f'  <a href="{esc(url)}" target="_blank">')
        parts.append("  " + piece)
        parts.append("  </a>")
        bx += bw + 12

    parts.append("</svg>")
    return "netstat", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 3 —  PROJECTS
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
    h = TITLE_H + LINE_H * n_rows + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
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
#  PANEL 4 —  STATS
# ═══════════════════════════════════════════════════════════════════

def render_stats():
    stats_w, stats_h = 380, 170
    streak_w, streak_h = 380, 195
    content_h = stats_h + 16 + streak_h
    inner_h = TITLE_H + 12 + content_h
    h = inner_h + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
    parts.append(title_bar(h, "github-stats"))

    stats_url = "https://github-stats-extended.vercel.app/api?username=Akileswaran04&show_icons=true&bg_color=0f172a&title_color=22d3ee&text_color=e6edf3&icon_color=22d3ee&border_color=22D3EE&hide_border=true"
    streak_url = "https://streak-stats.demolab.com/?user=Akileswaran04&background=0f172a&ring=22d3ee&fire=22d3ee&currStreakLabel=e6edf3&sideLabels=e6edf3&currStreakNum=22d3ee&sideNums=22d3ee&dates=7d8590&border=22D3EE"

    ix = (W - stats_w) / 2
    iy = TITLE_H + 12
    parts.append(f'  <image href="{stats_url}" xlink:href="{stats_url}" x="{ix:.0f}" y="{iy}" width="{stats_w}" height="{stats_h}" preserveAspectRatio="xMidYMid meet"/>')

    sy = iy + stats_h + 16
    sx = (W - streak_w) / 2
    parts.append(f'  <image href="{streak_url}" xlink:href="{streak_url}" x="{sx:.0f}" y="{sy}" width="{streak_w}" height="{streak_h}" preserveAspectRatio="xMidYMid meet"/>')

    parts.append("</svg>")
    return "stats", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 5 —  STACK  (skill pills)
# ═══════════════════════════════════════════════════════════════════

SKILLS = [
    ("C++", "#00599C"), ("Python", "#3776AB"), ("JavaScript", "#F7DF1E", "#000"),
    ("React", "#61DAFB", "#000"), ("Three.js", "#000000"), ("Node.js", "#339933"),
    ("FastAPI", "#009688"), ("Streamlit", "#FF4B4B"), ("PostgreSQL", "#4169E1"),
    ("Firebase", "#FFCA28", "#000"), ("XGBoost", "#150458"), ("TensorFlow", "#FF6F00"),
    ("PyTorch", "#EE4C2C"), ("scikit-learn", "#F7931E", "#000"),
    ("Git", "#F05032"), ("Docker", "#2496ED"),
]

def render_stack():
    per_row = 5
    rows = [SKILLS[i:i+per_row] for i in range(0, len(SKILLS), per_row)]
    n_rows = 2 + len(rows)  # host + section + skill rows
    h = TITLE_H + LINE_H * n_rows + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
    parts.append(title_bar(h, "skills"))

    y = TITLE_H + 30
    parts.append("  " + host_line(y))
    y += LINE_H
    parts.append("  " + section_header(y, "Technologies"))
    y += LINE_H

    for row in rows:
        tw = sum(len(s[0]) * 8.5 + 28 for s in row) + (len(row) - 1) * 10
        bx = (W - tw) / 2
        by = y + 10  # badge vertical centre
        for s in row:
            label, colour = s[0], s[1]
            tc = s[2] if len(s) > 2 else "#ffffff"
            piece, bw = pill(bx, by, label, colour, tc)
            parts.append("  " + piece)
            bx += bw + 10
        y += 28

    parts.append("</svg>")
    return "stack", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 6 —  BUILDING NOW
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
    h = TITLE_H + LINE_H * n_rows + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
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
#  PANEL 7 —  TAGLINE
# ═══════════════════════════════════════════════════════════════════

def render_tagline():
    lines = [
        'Full-Stack Developer | Applied ML',
        'Full-Stack x AI/ML — turning data into decisions',
    ]
    n_rows = 3  # host + 2 text lines
    h = TITLE_H + LINE_H * n_rows + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(h))
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
        render_whoami(),
        render_netstat(),
        render_projects(),
        render_stats(),
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
