#!/usr/bin/env python3
"""Generate a GitHub stats SVG card using the GitHub REST API.

Reads contributions.json for contribution data, and fetches user profile
+ repo stats from the GitHub API.  Outputs as local SVG (no external
service dependency).

Output: ../github-stats.svg
Replaces the external github-stats-extended.vercel.app service.

Cyber Cyan theme (matching contrib-heatmap):
  bg  #0d1117   bg2 #0f172a
  acc #22D3EE   mut #38BDF8   txt #e6edf3   dim #7d8590
"""
import datetime
import json
import os
import sys

import requests

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "github-stats.svg")

GH_PAT = os.environ.get("GH_PAT", "")
USERNAME = os.environ.get("GH_PROFILE_USER", "Akileswaran04")

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
H      = 220

TITLE_H = 30
PAD     = 30

# Unicode characters (must be valid in XML, unlike HTML entities)
MIDDOT = "\u00B7"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_num(n):
    """Format an integer with comma separators, or return string as-is."""
    if isinstance(n, int):
        return f"{n:,}"
    return str(n)


def fetch_stats():
    """Fetch user profile and repo stats from GitHub REST API."""
    headers = {"User-Agent": "profile-readme-bot/1.0"}
    if GH_PAT:
        headers["Authorization"] = f"Bearer {GH_PAT}"

    # User profile
    resp = requests.get(f"https://api.github.com/users/{USERNAME}", headers=headers, timeout=15)
    resp.raise_for_status()
    user = resp.json()

    # Repos (up to 100 for star count)
    resp = requests.get(
        f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=pushed",
        headers=headers, timeout=15
    )
    resp.raise_for_status()
    repos = resp.json()

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    total_repos = user.get("public_repos", 0)
    followers = user.get("followers", 0)
    following = user.get("following", 0)
    created = user.get("created_at", "")[:4]  # Year joined

    return {
        "repos": total_repos,
        "stars": total_stars,
        "forks": total_forks,
        "followers": followers,
        "following": following,
        "joined": created,
        "avatar": user.get("avatar_url", ""),
        "name": user.get("name", USERNAME),
    }


def render(stats, contrib_data):
    now = datetime.datetime.now(datetime.timezone.utc)
    gen_label = now.strftime("%Y-%m-%d %H:%M UTC")

    total_contrib = contrib_data.get("total_contributions", 0)
    active_days = contrib_data.get("active_days", 0)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"',
        f'viewBox="0 0 {W} {H}"',
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',

        # ── Defs ──
        '<defs>',
        f'<linearGradient id="sbg" x1="0" y1="0" x2="0" y2="1">',
        f'<stop offset="0" stop-color="{BG2}"/>',
        f'<stop offset="1" stop-color="{BG}"/></linearGradient>',
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
        f'text-anchor="middle">akileswaran04@github: ~/github-stats</text>',

        # ── Avatar initial ──
        f'<circle cx="55" cy="{TITLE_H + 85}" r="32"',
        f'fill="none" stroke="{ACCENT}" stroke-width="1.5" stroke-opacity="0.4"/>',
        f'<text x="55" y="{TITLE_H + 93}" text-anchor="middle"',
        f'fill="{ACCENT}" font-size="28" font-weight="700">{USERNAME[0].upper()}</text>',
    ]

    # ── Stat columns ──
    col_positions = [140, 315, 490, 665]

    # Row 1
    row1_labels = ["CONTRIBUTIONS", "REPOSITORIES", "FOLLOWERS", "STARS EARNED"]
    row1_icons  = ["~", "#", "@", "*"]
    row1_values = [total_contrib, stats["repos"], stats["followers"], stats["stars"]]

    for cx, label, icon, value in zip(col_positions, row1_labels, row1_icons, row1_values):
        parts.extend([
            f'<text x="{cx}" y="{TITLE_H + 38}" font-size="14" fill="{ACCENT}" opacity="0.6">{icon}</text>',
            f'<text x="{cx}" y="{TITLE_H + 58}" font-size="10" fill="{DIM}" font-weight="600">{esc(label)}</text>',
            f'<text x="{cx}" y="{TITLE_H + 92}" font-size="32" font-weight="700" fill="{TEXT}">{fmt_num(value)}</text>',
        ])

    # Row 2
    row2_labels = ["ACTIVE DAYS", "FORKS", "FOLLOWING", "JOINED"]
    row2_values = [active_days, stats["forks"], stats["following"], stats["joined"]]

    for cx, label, value in zip(col_positions, row2_labels, row2_values):
        parts.extend([
            f'<text x="{cx}" y="{TITLE_H + 118}" font-size="10" fill="{DIM}" font-weight="600">{esc(label)}</text>',
            f'<text x="{cx}" y="{TITLE_H + 145}" font-size="24" font-weight="600" fill="{MUTED}">{fmt_num(value)}</text>',
        ])

    # Separator
    parts.append(
f'<line x1="{PAD}" y1="{TITLE_H + 160}" x2="{W - PAD}" y2="{TITLE_H + 160}" '
f'stroke="{ACCENT}" stroke-opacity="0.15"/>'
    )

    # Footer
    parts.extend([
        f'<text x="{PAD}" y="{TITLE_H + 185}" font-size="12" fill="{ACCENT}"',
        f'font-weight="600">{esc(stats["name"])}</text>',
        f'<text x="{PAD}" y="{TITLE_H + 203}" font-size="9" fill="{DIM}" opacity="0.5">',
        f'GitHub API {MIDDOT} generated {esc(gen_label)}</text>',

        # Auth badge
        f'<rect x="{W - PAD - 120}" y="{TITLE_H + 172}" width="120" height="22" rx="4"',
        f'fill="none" stroke="{GREEN if GH_PAT else DIM}" stroke-width="0.8" opacity="0.5"/>',
        f'<text x="{W - PAD - 60}" y="{TITLE_H + 187}" text-anchor="middle" font-size="10"',
        f'fill="{GREEN if GH_PAT else DIM}" opacity="0.7">',
        f'{"API authenticated" if GH_PAT else "unauthenticated"}</text>',

        '</svg>',
    ])

    return "\n".join(parts)


if __name__ == "__main__":
    if not os.path.exists(IN_PATH):
        print("no contributions.json found — using empty defaults", file=sys.stderr)
        contrib_data = {"total_contributions": 0, "active_days": 0}
    else:
        contrib_data = json.load(open(IN_PATH))

    print(f"fetching GitHub stats for {USERNAME}...")
    stats = fetch_stats()
    print(f"  repos={stats['repos']} stars={stats['stars']} followers={stats['followers']}")

    svg = render(stats, contrib_data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
