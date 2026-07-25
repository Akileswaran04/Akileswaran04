#!/usr/bin/env python3
"""Generate glassmorphism panel SVGs for GitHub profile README sections.

Each panel bakes in a "liquid glass" effect:
  - Dark gradient background (#0d1117 → #0f172a)
  - Soft blurred colour blobs (cyan #22D3EE, secondary blue #38BDF8)
  - Semi-transparent white glass surface (6% opacity)
  - 1px semi-transparent white border (12% opacity)
  - A subtle top-edge highlight
  - Large border-radius (18 px)
  - Generous 28 px internal padding

Output files are written to the repo root as glass-*.svg.
Call without arguments to regenerate all panels.
"""

import html
import os

# ═══════════════════════════════════════════════════════════════════
#  THEME  —  Cyber Cyan
# ═══════════════════════════════════════════════════════════════════

BG    = "#0d1117"
BG2   = "#0f172a"
ACCENT= "#22D3EE"   # primary cyan
MUTED = "#38BDF8"   # secondary blue
INK   = "#e6edf3"   # body text
DIM   = "#7d8590"   # muted text

# ── Glass panel constants ───────────────────────────────────────
W      = 860         # panel width
PAD    = 28          # internal padding
R      = 18          # border-radius
LINE_H = 24          # base line height for content rows
H1     = 26          # heading font size
H2     = 14          # body font size / table cell

HERE   = os.path.dirname(os.path.abspath(__file__))
OUT    = HERE        # write SVGs to scripts/ alongside the .py

# ═══════════════════════════════════════════════════════════════════
#  GLASS BACKGROUND BUILDER
# ═══════════════════════════════════════════════════════════════════

def esc(s):
    return html.escape(s)


def glass_defs():
    return """\
  <defs>
    <linearGradient id="g-bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color=\"""" + BG2 + """\"/>
      <stop offset="1" stop-color=\"""" + BG + """\"/>
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


def glass_bg(w, h):
    """Return the glass background elements for a panel of *w* × *h*."""
    return f"""\
  <!-- Gradient background -->
  <rect width="{w}" height="{h}" rx="{R}" fill="url(#g-bg)"/>
  <!-- Colour blobs (simulating what blur-behind glass reveals) -->
  <circle cx="{w*0.18:.0f}" cy="{h*0.35:.0f}" r="{w*0.14:.0f}" fill="{ACCENT}" opacity="0.12" filter="url(#g-blur-lg)"/>
  <circle cx="{w*0.78:.0f}" cy="{h*0.65:.0f}" r="{w*0.10:.0f}" fill="{MUTED}"  opacity="0.10" filter="url(#g-blur-lg)"/>
  <circle cx="{w*0.50:.0f}" cy="{h*0.15:.0f}" r="{w*0.07:.0f}" fill="{ACCENT}" opacity="0.08" filter="url(#g-blur-sm)"/>
  <!-- Glass pane surface -->
  <rect x="0" y="0" width="{w}" height="{h}" rx="{R}" fill="#ffffff" fill-opacity="0.06"/>
  <!-- Glass border -->
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{R}" fill="none" stroke="#ffffff" stroke-opacity="0.18" stroke-width="1"/>
  <!-- Top light-catching highlight -->
  <rect x="2" y="2" width="{w-4}" height="6" rx="{R}" fill="url(#g-top)"/>"""


def heading(y, text):
    """Return a centred heading element at baseline *y*."""
    return f'<text x="{W/2}" y="{y:.0f}" fill="{ACCENT}" font-size="{H1}" font-weight="700" text-anchor="middle" font-family="ui-monospace,monospace">{esc(text)}</text>'


# ═══════════════════════════════════════════════════════════════════
#  PANEL 1 —  CONNECT  (social pill badges)
# ═══════════════════════════════════════════════════════════════════

def pill(x, y, text, bg_colour, text_colour="#ffffff"):
    """A coloured pill badge — returns width consumed."""
    tw = len(text) * 8.5 + 24
    return (
        f'<rect x="{x:.0f}" y="{y-9:.0f}" width="{tw:.0f}" height="24" rx="12" fill="{bg_colour}"/>'
        f'<text x="{x+tw/2:.0f}" y="{y+4:.0f}" fill="{text_colour}" font-size="12.5" '
        f'font-weight="600" text-anchor="middle" font-family="ui-monospace,monospace">'
        f'{esc(text)}</text>'
    ), tw


def render_connect():
    h = 120
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace,monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(W, h))
    parts.append(heading(PAD + H1, "🔗 Connect"))

    badges = [
        ("LinkedIn",  "#0A66C2"),
        ("GitHub",    "#181717"),
        ("LeetCode",  "#FFA116", "#000000"),
        ("SENTRI",    "#FF4B4B"),
    ]
    bx = PAD + 8
    by = PAD + H1 + 16 + 24  # baseline for badge row
    links = [
        ("https://linkedin.com/in/akileswaran-ammamuthu", badges[0]),
        ("https://github.com/Akileswaran04", badges[1]),
        ("https://leetcode.com/u/Akileswaran04/", badges[2]),
        ("https://sentri-final.streamlit.app", badges[3]),
    ]
    for url, b in links:
        label = b[0]
        colour = b[1]
        tc = b[2] if len(b) > 2 else "#ffffff"
        piece, bw = pill(bx, by, label, colour, tc)
        parts.append(f'  <a href="{esc(url)}" target="_blank">')
        parts.append("  " + piece)
        parts.append("  </a>")
        bx += bw + 12

    parts.append("</svg>")
    return "connect", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 2 —  PROJECTS  (table)
# ═══════════════════════════════════════════════════════════════════

PROJECTS = [
    ("01", "ODYSSEY",        "LLM · EBM · LangChain",                f'<tspan fill="{MUTED}">○ processing</tspan>'),
    ("02", "SENTRI ▸",       "Streamlit · FastAPI · XGBoost",        f'<tspan fill="{ACCENT}">● live</tspan>'),
    ("03", "Gridlock",       "LightGBM · XGBoost · Hackathon",       f'<tspan fill="{MUTED}">○ archive</tspan>'),
    ("04", "Riddle Rush ▸",  "React · Three.js · Supabase",          f'<tspan fill="{ACCENT}">● live</tspan>'),
    ("05", "DayLog",         "React · Node.js · Firebase",           f'<tspan fill="#34D399">✓ done</tspan>'),
]

def render_projects():
    n_rows = len(PROJECTS) + 1  # +1 for header
    row_h = 28
    table_h = n_rows * row_h + 12
    h = PAD + H1 + 16 + table_h + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace,monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(W, h))
    parts.append(heading(PAD + H1 - 2, "📌 Projects"))

    cols = [40, 160, 380, 120]  # ID, Name, Stack, Status widths
    col_starts = [PAD]
    for c in cols[:-1]:
        col_starts.append(col_starts[-1] + c)
    col_starts[1] += 8   # extra indent for name

    ty = PAD + H1 + 24   # table top baseline

    # Header
    headers = ["ID", "Name", "Stack", "Status"]
    for i, (cs, hdr) in enumerate(zip(col_starts, headers)):
        parts.append(f'  <text x="{cs}" y="{ty}" fill="{MUTED}" font-size="{H2}" font-weight="700">{hdr}</text>')
    ty += row_h

    # Rows
    links_map = {}
    for row in PROJECTS:
        pid, name, stack, status = row
        is_sentri = "SENTRI" in name and "▸" in name
        is_riddle = "Riddle Rush" in name and "▸" in name
        parts.append(f'  <text x="{col_starts[0]}" y="{ty}" fill="{DIM}" font-size="{H2}">{pid}</text>')
        if is_sentri:
            parts.append(f'  <a href="https://sentri-final.streamlit.app" target="_blank">')
            parts.append(f'    <text x="{col_starts[1]}" y="{ty}" fill="{ACCENT}" font-size="{H2}" font-weight="600">{esc(name)}</text>')
            parts.append(f'  </a>')
        elif is_riddle:
            parts.append(f'  <a href="https://csau.vercel.app" target="_blank">')
            parts.append(f'    <text x="{col_starts[1]}" y="{ty}" fill="{ACCENT}" font-size="{H2}" font-weight="600">{esc(name)}</text>')
            parts.append(f'  </a>')
        else:
            parts.append(f'  <text x="{col_starts[1]}" y="{ty}" fill="{INK}" font-size="{H2}" font-weight="600">{esc(name)}</text>')
        parts.append(f'  <text x="{col_starts[2]}" y="{ty}" fill="{INK}" font-size="{H2}">{esc(stack)}</text>')
        parts.append(f'  <text x="{col_starts[3]}" y="{ty}" font-size="{H2}">{status}</text>')
        ty += row_h

    parts.append("</svg>")
    return "projects", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 3 —  GITHUB STATS  (two stat images)
# ═══════════════════════════════════════════════════════════════════

def render_stats():
    # Use proper dimensions for each image
    stats_w = 400
    stats_h = 170
    streak_w = 400
    streak_h = 195
    gap = 20
    # Stack vertically: stats on top, streak below
    content_h = stats_h + 12 + streak_h
    h = PAD + H1 + 24 + content_h + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace,monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(W, h))
    parts.append(heading(PAD + H1 - 2, "📊 GitHub Stats"))

    iy = PAD + H1 + 24

    # GitHub stats card
    stats_url = "https://github-stats-extended.vercel.app/api?username=Akileswaran04&show_icons=true&bg_color=0f172a&title_color=22d3ee&text_color=e6edf3&icon_color=22d3ee&border_color=22D3EE&hide_border=true"
    # Centre stats card
    ix = (W - stats_w) / 2
    parts.append(f'  <image href="{stats_url}" xlink:href="{stats_url}" x="{ix:.0f}" y="{iy}" width="{stats_w}" height="{stats_h}" preserveAspectRatio="xMidYMid meet"/>')

    # Streak card below
    sy = iy + stats_h + 12
    sx = (W - streak_w) / 2
    streak_url = "https://streak-stats.demolab.com/?user=Akileswaran04&background=0f172a&ring=22d3ee&fire=22d3ee&currStreakLabel=e6edf3&sideLabels=e6edf3&currStreakNum=22d3ee&sideNums=22d3ee&dates=7d8590&border=22D3EE"
    parts.append(f'  <image href="{streak_url}" xlink:href="{streak_url}" x="{sx:.0f}" y="{sy}" width="{streak_w}" height="{streak_h}" preserveAspectRatio="xMidYMid meet"/>')

    parts.append("</svg>")
    return "stats", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 4 —  STACK  (skill pill badges)
# ═══════════════════════════════════════════════════════════════════

SKILLS = [
    ("C++",            "#00599C"),
    ("Python",         "#3776AB"),
    ("JavaScript",     "#F7DF1E", "#000000"),
    ("React",          "#61DAFB", "#000000"),
    ("Three.js",       "#000000"),
    ("Node.js",        "#339933"),
    ("FastAPI",        "#009688"),
    ("Streamlit",      "#FF4B4B"),
    ("PostgreSQL",     "#4169E1"),
    ("Firebase",       "#FFCA28", "#000000"),
    ("XGBoost",        "#150458"),
    ("TensorFlow",     "#FF6F00"),
    ("PyTorch",        "#EE4C2C"),
    ("scikit-learn",   "#F7931E", "#000000"),
    ("Git",            "#F05032"),
    ("Docker",         "#2496ED"),
]

def render_stack():
    # Lay out pills in rows of ~5 at W=860
    per_row = 5
    rows = [SKILLS[i:i+per_row] for i in range(0, len(SKILLS), per_row)]
    pill_h = 26
    row_gap = 14
    table_h = len(rows) * (pill_h + row_gap)
    h = PAD + H1 + 16 + table_h + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace,monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(W, h))
    parts.append(heading(PAD + H1 - 2, "🛠️ Stack"))

    py = PAD + H1 + 20
    for row in rows:
        # Compute total width of this row to centre it
        tw = sum(len(s[0]) * 8.5 + 28 for s in row) + (len(row) - 1) * 10
        bx = (W - tw) / 2
        by = py + pill_h // 2 + 2  # text baseline
        for s in row:
            label = s[0]
            colour = s[1]
            tc = s[2] if len(s) > 2 else "#ffffff"
            piece, bw = pill(bx, by, label, colour, tc)
            parts.append("  " + piece)
            bx += bw + 10
        py += pill_h + row_gap

    parts.append("</svg>")
    return "stack", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 5 —  BUILDING NOW  (table)
# ═══════════════════════════════════════════════════════════════════

BUILDING = [
    ("001", "SENTRI",      "Streamlit · FastAPI · XGBoost",  "42%"),
    ("002", "Riddle Rush", "React · Three.js · Supabase",     "35%"),
    ("003", "ODYSSEY",     "LLM · EBM · LangChain",          "38%"),
]

def render_building():
    n_rows = len(BUILDING) + 1
    row_h = 28
    table_h = n_rows * row_h + 12
    h = PAD + H1 + 16 + table_h + PAD

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace,monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(W, h))
    parts.append(heading(PAD + H1 - 2, "🚧 Building now"))

    cols = [50, 160, 440, 80]
    col_starts = [PAD]
    for c in cols[:-1]:
        col_starts.append(col_starts[-1] + c)
    col_starts[1] += 8

    ty = PAD + H1 + 24
    headers = ["PID", "Process", "Stack", "CPU"]
    for cs, hdr in zip(col_starts, headers):
        parts.append(f'  <text x="{cs}" y="{ty}" fill="{MUTED}" font-size="{H2}" font-weight="700">{hdr}</text>')
    ty += row_h

    for row in BUILDING:
        pid, name, stack, cpu = row
        parts.append(f'  <text x="{col_starts[0]}" y="{ty}" fill="{DIM}" font-size="{H2}">{pid}</text>')
        parts.append(f'  <text x="{col_starts[1]}" y="{ty}" fill="{INK}" font-size="{H2}" font-weight="600">{name}</text>')
        parts.append(f'  <text x="{col_starts[2]}" y="{ty}" fill="{INK}" font-size="{H2}">{stack}</text>')
        parts.append(f'  <text x="{col_starts[3]}" y="{ty}" fill="{ACCENT}" font-size="{H2}" font-weight="600">{cpu}</text>')
        ty += row_h

    parts.append("</svg>")
    return "building", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  PANEL 6 —  TAGLINE
# ═══════════════════════════════════════════════════════════════════

def render_tagline():
    lines = [
        'Full-Stack Developer | Applied ML',
        'Full-Stack × AI/ML — turning data into decisions',
    ]
    h = PAD + H1 + 16 + len(lines) * 26 + PAD + 20

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" font-family="ui-monospace,monospace">']
    parts.append(glass_defs())
    parts.append(glass_bg(W, h))
    parts.append(heading(PAD + H1 - 2, "💬 Tagline"))

    ty = PAD + H1 + 30
    for i, line in enumerate(lines):
        colour = ACCENT if i == 0 else INK
        sz = 16 if i == 0 else 14
        parts.append(f'  <text x="{W/2}" y="{ty}" fill="{colour}" font-size="{sz}" text-anchor="middle" font-weight="500">{esc(line)}</text>')
        ty += 26

    parts.append("</svg>")
    return "tagline", "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    panels = [
        render_connect(),
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
