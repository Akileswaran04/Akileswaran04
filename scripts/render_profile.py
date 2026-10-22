#!/usr/bin/env python3
"""Render every profile panel and README.md.

Inputs:  data/profile.json        (hand-edited: who you are, projects, stack, journey)
         data/contributions.json  (written daily by fetch_contributions.py)
         data/portrait.txt        (ASCII portrait, written by make_portrait.py)
Outputs: assets/*.svg + README.md

  python scripts/render_profile.py                         # theme from profile.json
  python scripts/render_profile.py --theme amber --out previews/amber   # try a theme

GitHub shows these SVGs through <img>, so there is no JS and no hover: every
animation is CSS @keyframes or SMIL. Elements keep their *final* state as the
base style and animate *from* the hidden state, so prefers-reduced-motion
(which switches CSS animations off) still shows a complete panel.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
import random
from xml.sax.saxutils import escape

import theme as th

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
W = 860
CW = 0.6  # monospace advance width, in em


def esc(s):
    return escape(str(s), {'"': "&quot;"})


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def svg(theme, h, label, body, css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" '
            f'viewBox="0 0 {W} {h}" role="img" aria-label="{esc(label)}">'
            f"<style><![CDATA[{th.css(theme)}{css}]]></style>{FX}{body}</svg>")


def frame(h, title, sub=""):
    """Panel card with a centred '✿ About Me ✿' heading (last word glows) and a subtitle."""
    *head, last = title.split()
    adv = 20 * CW
    x0 = W / 2 - len(title) * adv / 2
    x_last = x0 + (len(title) - len(last)) * adv
    return (f'<rect class="f-bg s-line" x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="14"/>'
            f'<g transform="translate({x0 - 20:.0f},31) scale(.75)" filter="url(#glow)"><use href="#fl"/></g>'
            f'<g transform="translate({x0 + len(title) * adv + 20:.0f},31) scale(.75)" filter="url(#glow)"><use href="#fl"/></g>'
            f'<text class="f-ink" x="{x0:.1f}" y="38" font-size="20" font-weight="800" '
            f'textLength="{len(" ".join(head)) * adv:.1f}">{esc(" ".join(head))}</text>'
            f'<text class="f-acc" x="{x_last:.1f}" y="38" font-size="20" font-weight="800" '
            f'textLength="{len(last) * adv:.1f}" filter="url(#glow)">{esc(last)}</text>'
            f'<text class="f-dim" x="{W / 2}" y="57" font-size="11.5" text-anchor="middle">{esc(sub)}</text>')


RISE = "@keyframes rise{from{opacity:0;transform:translateY(10px)}}"
FADE = "@keyframes fade{from{opacity:0}}"
BLINK = "@keyframes blink{50%{opacity:0}}"
POP = ".pop{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.2,.8,.2,1.3) both}" \
      "@keyframes pop{from{opacity:0;transform:scale(.2)}}"


# ── shared sakura / neon pieces ─────────────────────────────────────────

FX = ('<defs>'
      '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/>'
      '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
      '<filter id="glow2" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="10" result="b"/>'
      '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
      '<linearGradient id="pg" x1="0" x2="1"><stop offset="0" style="stop-color:var(--acc)"/>'
      '<stop offset="1" style="stop-color:var(--acc2)"/></linearGradient>'
      '<path id="pt" d="M0,0 C-5,-3 -5.5,-9 -1.6,-11.5 L0,-9.6 L1.6,-11.5 C5.5,-9 5,-3 0,0Z"/>'
      '<g id="fl">' + "".join(f'<use href="#pt" class="f-acc3" transform="rotate({k * 72})"/>' for k in range(5)) +
      '<circle class="f-acc" r="2.6"/></g></defs>')

SAKURA_CSS = (".sway{animation:sway 7s ease-in-out infinite alternate}"
              "@keyframes sway{from{transform:rotate(-1.5deg)}to{transform:rotate(1.5deg)}}"
              ".fall{opacity:0;transform-box:fill-box;transform-origin:center;animation:fall linear infinite}"
              "@keyframes fall{0%{opacity:0;transform:translate(0,0) rotate(0)}10%{opacity:.9}85%{opacity:.8}"
              "100%{opacity:0;transform:translate(var(--dx),var(--dy)) rotate(420deg)}}")


def branch(x, y, s=1.0, flip=False, t0=0.3):
    """A blossoming cherry branch; base at (x, y), growing up and right (or left)."""
    paths = [("M0,0 C40,-10 70,-40 110,-60 S170,-100 200,-120", 3.2), ("M70,-38 C80,-60 95,-75 100,-95", 2.2),
             ("M120,-64 C140,-58 160,-50 185,-55", 2), ("M150,-85 C155,-100 165,-110 170,-125", 1.6)]
    blooms = [(60, -30, .8), (85, -70, .7), (110, -60, 1.1), (100, -95, 1), (140, -80, .9), (130, -100, .6),
              (160, -52, .7), (185, -55, 1), (170, -125, .9), (200, -120, .8)]
    g = "".join(f'<path class="s-acc" d="{d}" fill="none" stroke-width="{w}" stroke-linecap="round" opacity=".55"/>'
                for d, w in paths)
    g += '<g filter="url(#glow)">' + "".join(
        f'<g transform="translate({bx},{by}) scale({bs})"><use href="#fl" class="pop" '
        f'style="animation-delay:{t0 + i * .12:.2f}s"/></g>' for i, (bx, by, bs) in enumerate(blooms)) + "</g>"
    return f'<g transform="translate({x},{y}) scale({-s if flip else s},{s})"><g class="sway">{g}</g></g>'


def petals(x0, x1, y0, y1, n, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, s, dur = rnd.uniform(x0, x1), rnd.uniform(.5, .9), rnd.uniform(6, 11)
        out.append(f'<g transform="translate({x:.0f},{y0}) scale({s:.2f})"><use href="#pt" class="f-acc3 fall" '
                   f'style="--dx:{rnd.uniform(-70, 20) / s:.0f}px;--dy:{(y1 - y0) / s:.0f}px;'
                   f'animation-duration:{dur:.1f}s;animation-delay:{-rnd.uniform(0, dur):.1f}s"/></g>')
    return "".join(out)


# ── 1. banner: landing-page hero with navbar, typed roles, neon moon ────

def typed_roles(x0, y, fs, roles):
    """Type, hold, erase each role in turn, forever (SMIL, so it also runs in <img>)."""
    adv = fs * CW
    plan, t = [], 0.0
    for r in roles:
        ev = [(t + k * .07, k) for k in range(1, len(r) + 1)]
        end = ev[-1][0] + 2.2
        ev += [(end + (len(r) - k) * .03, k) for k in range(len(r) - 1, -1, -1)]
        plan.append(ev)
        t = ev[-1][0] + .35
    total = t

    def anim(attr, events, base):
        times, vals = [0.0], [base]
        for tt, k in events:
            times.append(tt / total)
            vals.append(base + k * adv)
        times.append(1.0)
        vals.append(base)
        return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{total:.2f}s" repeatCount="indefinite" '
                f'keyTimes="{";".join(f"{x:.4f}" for x in times)}" values="{";".join(f"{v:.1f}" for v in vals)}"/>')

    out = []
    for i, (r, ev) in enumerate(zip(roles, plan)):
        out.append(f'<clipPath id="ro{i}"><rect x="{x0}" y="{y - fs}" width="0" height="{fs * 1.5}">'
                   f'{anim("width", ev, 0)}</rect></clipPath>'
                   f'<text class="f-acc" clip-path="url(#ro{i})" x="{x0}" y="{y}" font-size="{fs}" font-weight="700" '
                   f'textLength="{len(r) * adv:.1f}" lengthAdjust="spacing" filter="url(#glow)">{esc(r)}</text>')
    caret_ev = sorted(e for ev in plan for e in ev)
    out.append(f'<rect class="f-acc caret" x="{x0}" y="{y - fs + 3}" width="3" height="{fs}">'
               f'{anim("x", caret_ev, x0)}</rect>')
    return "".join(out)


def banner(p, theme):
    h = 350
    names = [theme] if isinstance(theme, str) else theme
    first = p["name"].split()[0]
    css = (POP + SAKURA_CSS + RISE + BLINK + ".up{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}"
           ".caret{animation:blink 1s steps(1) infinite}")
    body = [f'<clipPath id="card"><rect width="{W}" height="{h}" rx="14"/></clipPath>',
            f'<rect class="f-bg s-line" x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="14"/>']

    # navbar pill (labels are decoration; the right-hand pill is the theme toggle)
    nx, nw = 150, 560
    body.append(f'<rect class="f-bg2 s-line" x="{nx}" y="16" width="{nw}" height="36" rx="18"/>'
                f'<text x="{nx + 22}" y="39" font-size="16" font-weight="800"><tspan class="f-acc">AK</tspan>'
                f'<tspan class="f-ink">I</tspan></text>')
    for i, lab in enumerate(("home", "about", "projects", "skills", "journey")):
        x = nx + 92 + i * 66
        body.append(f'<text class="f-{"acc" if i == 0 else "ink"}" x="{x}" y="38" font-size="11.5" '
                    f'font-weight="700" text-anchor="middle">{lab.upper()}</text>')
        if i == 0:
            body.append(f'<rect class="f-acc" x="{x - 17}" y="43" width="34" height="2" rx="1"/>')
    kw = 62
    sw = kw * len(names) if len(names) > 1 else 112
    tx = nx + nw - 6 - sw
    body.append(f'<rect x="{tx}" y="21" width="{sw}" height="26" rx="13" fill="url(#pg)" filter="url(#glow)"/>')
    if len(names) > 1:  # knob slides in sync with the palette morph
        n = len(names)
        f = th.FADE / th.cycle_seconds(n)
        times, vals = [], []
        for i in range(n):
            times += [i / n, (i + 1) / n - f]
            vals += [f"{i * kw},0"] * 2
        times.append(1)
        vals.append("0,0")
        body.append(f'<rect class="f-bg" x="{tx + 3}" y="24" width="{kw - 6}" height="20" rx="10" opacity=".35">'
                    f'<animateTransform attributeName="transform" type="translate" values="{";".join(vals)}" '
                    f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" dur="{th.cycle_seconds(n)}s" '
                    f'repeatCount="indefinite"/></rect>')
        body += [f'<text class="f-bg" x="{tx + kw * i + kw / 2}" y="38" font-size="11.5" font-weight="800" '
                 f'text-anchor="middle">{esc(nm)}</text>' for i, nm in enumerate(names)]
    else:
        body.append(f'<text class="f-bg" x="{tx + sw / 2}" y="38" font-size="11.5" font-weight="800" '
                    f'text-anchor="middle">OPEN TO WORK</text>')

    # left column
    hi = f"Hi, I'm {first}"
    hi_end = 84 + len(hi) * 34 * CW
    prefix = "I'm a "
    body.append(
        f'<g class="up" style="animation-delay:.1s"><text class="f-dim" x="56" y="110" font-size="12" '
        f'letter-spacing="2" font-weight="700">{esc(p["name"].upper())}</text></g>'
        f'<g class="up" style="animation-delay:.25s">'
        f'<g transform="translate(66,140) scale(.9)" filter="url(#glow)"><use href="#fl"/></g>'
        f'<text class="f-ink" x="84" y="152" font-size="34" font-weight="800" '
        f'textLength="{len(hi) * 34 * CW:.1f}">{esc(hi)}</text>'
        f'<g transform="translate({hi_end + 16:.0f},140) scale(.9)" filter="url(#glow)"><use href="#fl"/></g></g>'
        f'<text class="f-acc2" x="56" y="194" font-size="24" font-weight="700">{prefix}</text>'
        + typed_roles(56 + len(prefix) * 24 * CW, 194, 24, p["roles"]) +
        f'<g class="up" style="animation-delay:.5s">'
        f'<text class="f-dim" x="56" y="230" font-size="13">{esc(p["education"])} · {esc(p["location"])}</text>'
        f'<text class="f-dim" x="56" y="250" font-size="13">now {esc(p["now"][0])}</text></g>')
    btn = f"● open to {p['open_to']}"
    bw = len(btn) * 13 * CW + 40
    body.append(f'<g class="up" style="animation-delay:.7s">'
                f'<rect x="56" y="266" width="{bw:.0f}" height="34" rx="17" fill="url(#pg)" filter="url(#glow)"/>'
                f'<text class="f-bg" x="{56 + bw / 2:.0f}" y="288" font-size="13" font-weight="800" '
                f'text-anchor="middle">{esc(btn)}</text></g>')

    # right: neon moon + blossom branch + falling petals (instead of a portrait)
    body.append(f'<g class="up" style="animation-delay:.2s">'
                f'<circle class="f-acc" cx="700" cy="168" r="96" opacity=".08"/>'
                f'<circle class="s-acc" cx="700" cy="168" r="96" fill="none" stroke-width="2" filter="url(#glow2)"/>'
                f'<circle class="s-acc2" cx="700" cy="168" r="78" fill="none" stroke-width="1" opacity=".4" '
                f'stroke-dasharray="2 6"/></g>'
                + branch(560, 268, 1.25) + petals(560, 840, 60, 300, 12, 3))

    # bottom strip: the whole stack scrolling past
    items = [it for g in p["stack"] for it in g["items"]]
    adv, gap = 12 * CW, 44
    xs, x = [], 0.0
    for it in items:
        xs.append(x)
        x += len(it) * adv + gap
    copy = x
    strip = "".join(f'<circle class="f-acc" cx="{off + x0 + 4:.1f}" cy="{h - 23}" r="3.5" filter="url(#glow)"/>'
                    f'<text class="f-ink" x="{off + x0 + 14:.1f}" y="{h - 19}" font-size="12">{esc(it)}</text>'
                    for off in (0, copy) for x0, it in zip(xs, items))
    css += f".mq{{animation:mq {copy / 28:.1f}s linear infinite}}@keyframes mq{{to{{transform:translateX(-{copy:.0f}px)}}}}"
    body.append(f'<g clip-path="url(#card)"><rect class="f-bg2" x="0" y="{h - 44}" width="{W}" height="44"/>'
                f'<rect x="0" y="{h - 44}" width="{W}" height="2" fill="url(#pg)" opacity=".7"/>'
                f'<g class="mq">{strip}</g></g>')

    label = f'{p["name"]}: {p["headline"]}. Open to {p["open_to"]}. Now {p["now"][0]}.'
    return svg(theme, h, label, "".join(body), css), label


# ── 2. hero: decrypting ASCII portrait + typed terminal session ──────────

GLYPHS = "01<>/\\{}[]#$%&*+=?"


def portrait_rows():
    with open(os.path.join(ROOT, "data", "portrait.txt"), encoding="utf-8") as f:
        rows = [r.rstrip() for r in f.read().split("\n")]
    while rows and not rows[0].strip():
        rows.pop(0)
    while rows and not rows[-1].strip():
        rows.pop()
    left = min(len(r) - len(r.lstrip()) for r in rows if r.strip())
    right = max(len(r) for r in rows)
    return [r[left:].ljust(right - left) for r in rows]


def hero(p, theme):
    rows = portrait_rows()
    cols = len(rows[0])
    px, top, pw = 24, 72, 330
    fs = pw / cols / CW
    lh = fs * 1.13
    ph = len(rows) * lh
    reveal = 2.6
    rnd = random.Random(7)

    def scramble(r):
        return "".join(" " if c == " " else rnd.choice(GLYPHS) for c in r)

    art = []
    tl = f'font-size="{fs:.2f}" textLength="{pw}" lengthAdjust="spacing" xml:space="preserve"'
    for i, r in enumerate(rows):
        y = top + (i + 1) * lh
        d = 0.3 + reveal * i / len(rows)
        art.append(
            f'<g class="sc" style="animation-duration:{d:.2f}s">'
            f'<text class="f-acc fa" x="{px}" y="{y:.1f}" {tl}>{esc(scramble(r))}</text>'
            f'<text class="f-acc fb" x="{px}" y="{y:.1f}" {tl}>{esc(scramble(r))}</text></g>'
            f'<text class="f-acc3 pr" x="{px}" y="{y:.1f}" {tl} style="animation-delay:{d:.2f}s">{esc(r)}</text>')
    beam = f'<rect class="f-acc bm" x="{px - 4}" y="{top}" width="{pw + 8}" height="2" rx="1"/>'

    # terminal
    tx = px + pw + 36
    tfs, tlh = 14, 27
    adv = tfs * CW
    kv = [("role", p["headline"]), ("edu", p["education"]), ("based", p["location"]), ("open", p["open_to"])]
    script = [("cmd", "whoami"), ("name", p["name"]),
              ("cmd", "cat profile.txt"), *[("kv", k, v) for k, v in kv],
              ("cmd", "cat now.txt"), *[("now", n) for n in p["now"]],
              ("cmd", None)]
    n_lines = len(script)
    ty = top + max(0, (ph - n_lines * tlh) / 2) + tfs
    out, t, clip_id = [], 0.4, 0
    for line in script:
        kind = line[0]
        if kind == "cmd":
            cmd = line[1]
            out.append(f'<text class="f-acc2 o" x="{tx}" y="{ty:.1f}" font-size="{tfs}" '
                       f'style="animation-delay:{t:.2f}s">❯</text>')
            if cmd is None:
                out.append(f'<g class="o" style="animation-delay:{t:.2f}s"><rect class="f-acc caret" '
                           f'x="{tx + 2 * adv:.1f}" y="{ty - tfs + 2:.1f}" width="{adv:.1f}" height="{tfs + 2}"/></g>')
                break
            n = len(cmd)
            vals = ";".join(f"{k * adv:.1f}" for k in range(n + 1))
            dur = 0.055 * (n + 1)
            x0 = tx + 2 * adv
            out.append(
                f'<clipPath id="ty{clip_id}"><rect x="{x0:.1f}" y="{ty - tfs:.1f}" width="0" height="{tfs * 1.6:.1f}">'
                f'<animate attributeName="width" values="{vals}" dur="{dur:.2f}s" begin="{t + .15:.2f}s" '
                f'calcMode="discrete" fill="freeze"/></rect></clipPath>'
                f'<text class="f-ink" clip-path="url(#ty{clip_id})" x="{x0:.1f}" y="{ty:.1f}" font-size="{tfs}" '
                f'textLength="{n * adv:.1f}" lengthAdjust="spacing">{esc(cmd)}</text>')
            clip_id += 1
            t += dur + 0.35
        elif kind == "name":
            out.append(f'<text class="f-acc o" x="{tx}" y="{ty:.1f}" font-size="18" font-weight="700" '
                       f'style="animation-delay:{t:.2f}s">{esc(line[1])}</text>')
            t += 0.25
        elif kind == "kv":
            out.append(f'<text class="o" x="{tx}" y="{ty:.1f}" font-size="{tfs}" style="animation-delay:{t:.2f}s">'
                       f'<tspan class="f-dim">{esc(line[1].ljust(7))}</tspan>'
                       f'<tspan class="f-ink" x="{tx + 7 * adv:.1f}">{esc(line[2])}</tspan></text>')
            t += 0.14
        elif kind == "now":
            out.append(f'<text class="o" x="{tx}" y="{ty:.1f}" font-size="{tfs}" style="animation-delay:{t:.2f}s">'
                       f'<tspan class="f-acc">→ </tspan><tspan class="f-ink">{esc(line[1])}</tspan></text>')
            t += 0.14
        ty += tlh

    h = int(max(top + ph, ty) + 30)
    css = (FADE + BLINK + RISE +
           ".pr{animation:fade .25s ease both}"
           ".sc{opacity:0;animation-name:on;animation-timing-function:steps(1)}"
           "@keyframes on{from,to{opacity:1}}"
           ".fa{animation:fl .18s steps(1) infinite}.fb{animation:fl .18s steps(1) -.09s infinite}"
           "@keyframes fl{50%{opacity:0}}"
           f".bm{{opacity:0;animation:bm {reveal}s linear .3s both}}"
           f"@keyframes bm{{0%{{opacity:.9;transform:translateY(0)}}96%{{opacity:.9;transform:translateY({ph:.0f}px)}}"
           f"100%{{opacity:0;transform:translateY({ph:.0f}px)}}}}"
           ".o{animation:o .3s ease both}@keyframes o{from{opacity:0;transform:translateX(-6px)}}"
           ".caret{animation:blink 1s steps(1) infinite}" + SAKURA_CSS)
    body = (frame(h, "About Me", f"~/{p['handle']} — whoami") +
            f'<g filter="url(#glow)">{"".join(art)}</g>' + beam +
            f'<line class="s-line" x1="{tx - 18}" y1="{top + 8}" x2="{tx - 18}" y2="{h - 22}" stroke-dasharray="2 4"/>' +
            "".join(out) + petals(tx, W - 20, top, h - 20, 7, 5))
    label = (f"ASCII portrait of {p['name']} beside a terminal: {p['headline']}; {p['education']}; "
             f"{p['location']}; open to {p['open_to']}.")
    return svg(theme, h, label, body, css), label


# ── 3. projects: carousel with a build pipeline per project ──────────────

STAGES = ("plan", "build", "test", "ship")
STATUS = {"live": ("acc2", "● live"), "building": ("acc", "◐ building"),
          "shipped": ("acc3", "✓ shipped"), "archived": ("dim", "▣ archived")}


def projects(p, theme):
    h, per = 300, 4.0
    items = p["projects"]
    n = len(items)
    cyc = per * n
    a, b, c = 2.0, 100 / n - 2.0, 100 / n
    css = (f".sl{{animation:sl {cyc}s infinite backwards}}"
           f"@keyframes sl{{0%{{opacity:0;transform:translateX(20px)}}{a}%{{opacity:1;transform:none}}"
           f"{b}%{{opacity:1;transform:none}}{c}%{{opacity:0;transform:translateX(-20px)}}100%{{opacity:0}}}}"
           f".st{{animation:st {cyc}s infinite backwards}}"
           f"@keyframes st{{0%{{opacity:0}}{a}%{{opacity:1}}{b}%{{opacity:1}}{c}%{{opacity:0}}100%{{opacity:0}}}}"
           ".pl{transform-box:fill-box;transform-origin:center;animation:pl 1.4s ease-out infinite}"
           "@keyframes pl{from{opacity:.9;transform:scale(1)}to{opacity:0;transform:scale(2.6)}}"
           "@media (prefers-reduced-motion:reduce){.sl:not(.s0),.dt:not(.d0){display:none}}")
    slides = []
    for i, pr in enumerate(items):
        d0 = i * per
        col, stat = STATUS.get(pr["status"], ("dim", pr["status"]))
        g = [f'<text class="f-line" x="40" y="150" font-size="78" font-weight="800">{i + 1:02d}</text>',
             f'<text class="f-ink" x="190" y="96" font-size="30" font-weight="800">{esc(pr["name"])}</text>',
             f'<text class="f-{col}" x="{W - 40}" y="94" font-size="13.5" text-anchor="end">{esc(stat)}</text>',
             f'<text class="f-dim" x="190" y="124" font-size="15">{esc(pr["tagline"])}</text>']
        cx = 190
        for s in pr["stack"]:
            w = len(s) * 12 * CW + 18
            g.append(f'<rect class="f-bg2 s-line" x="{cx}" y="140" width="{w:.0f}" height="22" rx="11"/>'
                     f'<text class="f-acc3" x="{cx + w / 2:.0f}" y="155" font-size="12" text-anchor="middle">{esc(s)}</text>')
            cx += w + 8
        sx, gap, sy = 200, 160, 212
        for k, name in enumerate(STAGES):
            x = sx + k * gap
            done, cur = k < pr["stage"], k == pr["stage"]
            if k:
                g.append(f'<line class="s-line" x1="{x - gap + 10}" y1="{sy}" x2="{x - 10}" y2="{sy}" stroke-width="2"/>')
                if done:
                    g.append(f'<line class="s-acc2 st" x1="{x - gap + 10}" y1="{sy}" x2="{x - 10}" y2="{sy}" '
                             f'stroke-width="2" style="animation-delay:{d0 + .3 + k * .3:.2f}s"/>')
            g.append(f'<circle class="f-bg s-line" cx="{x}" cy="{sy}" r="8" stroke-width="2"/>')
            if done:
                g.append(f'<circle class="f-acc2 st" cx="{x}" cy="{sy}" r="8" style="animation-delay:{d0 + .35 + k * .3:.2f}s"/>')
            elif cur:
                g.append(f'<circle class="s-acc pl" cx="{x}" cy="{sy}" r="8" fill="none" stroke-width="2" filter="url(#glow)"/>'
                         f'<circle class="f-acc" cx="{x}" cy="{sy}" r="5"/>')
            g.append(f'<text class="f-{"ink" if done or cur else "dim"}" x="{x}" y="{sy + 30}" font-size="12" '
                     f'text-anchor="middle">{name}</text>')
        slides.append(f'<g class="sl s{i}" style="animation-delay:{d0}s">{"".join(g)}</g>')
    dots = []
    for i in range(n):
        x = W / 2 + (i - (n - 1) / 2) * 18
        dots.append(f'<circle class="f-line" cx="{x}" cy="{h - 22}" r="4"/>'
                    f'<circle class="f-acc st dt d{i}" cx="{x}" cy="{h - 22}" r="4" style="animation-delay:{i * per}s"/>')
    body = frame(h, "My Projects", "what I've shipped and what's in the pipeline") + "".join(slides) + "".join(dots)
    label = "Projects: " + "; ".join(f'{x["name"]}, {x["tagline"]} ({x["status"]})' for x in items) + "."
    return svg(theme, h, label, body, css), label


# ── 4. flagship: animated architecture flow ─────────────────────────────

def flagship(p, theme):
    f = p["flagship"]
    pr = next(x for x in p["projects"] if x["name"] == f["project"])
    nodes = f["flow"]
    h, bw, bh, yc = 250, 150, 64, 170
    n = len(nodes)
    gap = (W - 80 - n * bw) / max(n - 1, 1)
    xs = [40 + i * (bw + gap) for i in range(n)]
    col, stat = STATUS.get(pr["status"], ("dim", pr["status"]))
    css = (RISE + ".nd{animation:rise .6s cubic-bezier(.2,.8,.2,1) both}"
           ".fl{stroke-dasharray:3 7;animation:fl .8s linear infinite}@keyframes fl{to{stroke-dashoffset:-10}}")
    body = [frame(h, "Flagship Build", f"how {f['project']} works"),
            f'<text class="f-ink" x="40" y="76" font-size="24" font-weight="800">{esc(pr["name"])}</text>',
            f'<text class="f-dim" x="40" y="100" font-size="14">{esc(pr["tagline"])}</text>',
            f'<text class="f-{col}" x="{W - 40}" y="76" font-size="13.5" text-anchor="end">{esc(stat)}</text>']
    for i in range(n - 1):
        x1, x2 = xs[i] + bw, xs[i + 1]
        body.append(f'<line class="s-line" x1="{x1}" y1="{yc}" x2="{x2}" y2="{yc}" stroke-width="2"/>'
                    f'<line class="s-acc fl" x1="{x1}" y1="{yc}" x2="{x2}" y2="{yc}" stroke-width="2"/>')
    path = f"M{xs[0] + bw / 2},{yc} L{xs[-1] + bw / 2},{yc}"
    for k in range(3):  # packets travel under the boxes, so they look like they pass through each stage
        body.append(f'<circle class="f-acc" r="4" filter="url(#glow)"><animateMotion path="{path}" dur="4.5s" '
                    f'begin="{k * 1.5}s" repeatCount="indefinite"/></circle>')
    for i, (x, nd) in enumerate(zip(xs, nodes)):
        body.append(f'<g class="nd" style="animation-delay:{.2 + i * .2:.1f}s">'
                    f'<rect class="f-bg2 s-{"acc" if i in (0, n - 1) else "line"}" x="{x}" y="{yc - bh / 2}" '
                    f'width="{bw}" height="{bh}" rx="8" stroke-width="1.5"/>'
                    f'<text class="f-ink" x="{x + bw / 2}" y="{yc - 3}" font-size="15" font-weight="700" '
                    f'text-anchor="middle">{esc(nd["label"])}</text>'
                    f'<text class="f-dim" x="{x + bw / 2}" y="{yc + 17}" font-size="11.5" '
                    f'text-anchor="middle">{esc(nd["sub"])}</text></g>')
    label = f'{pr["name"]} architecture: ' + " → ".join(nd["label"] for nd in nodes) + "."
    return svg(theme, h, label, "".join(body), css), label


# ── 5. stack: rotating orbits + readable legend ─────────────────────────

def stack(p, theme):
    groups = p["stack"][:4]
    n = len(groups)
    h, cx, cy, r0, r1 = 480, 240, 268, 90, 188
    radii = [r0 + i * (r1 - r0) / max(n - 1, 1) for i in range(n)]
    speeds, cols = (40, 60, 80, 100), ("acc", "acc2", "acc3", "ink")
    css = (FADE + ".r{animation:spin linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
           ".lg{animation:fade .6s ease both}")
    css += POP + SAKURA_CSS
    body = [frame(h, "My Skills", "what I build with"), petals(500, W - 20, 70, h - 20, 6, 9)]
    for gi, grp in enumerate(groups):
        r, sp, col = radii[gi], speeds[gi], cols[gi]
        rev = gi % 2 == 1
        items = grp["items"]
        ring = [f'<circle class="s-line" r="{r}" fill="none" stroke-dasharray="2 5"/>']
        for k, it in enumerate(items):
            ang = 2 * math.pi * k / len(items) + gi * 0.5
            lx, ly = r * math.cos(ang), r * math.sin(ang)
            w = len(it) * 11.5 * CW + 16
            ring.append(f'<g transform="translate({lx:.1f},{ly:.1f})"><g class="r" style="animation-duration:{sp}s;'
                        f'animation-direction:{"normal" if rev else "reverse"}">'
                        f'<rect class="f-bg2 s-{col}" x="{-w / 2:.1f}" y="-10" width="{w:.1f}" height="20" rx="10"/>'
                        f'<text class="f-ink" y="4" font-size="11.5" text-anchor="middle">{esc(it)}</text></g></g>')
        body.append(f'<g transform="translate({cx},{cy})"><g class="r" style="animation-duration:{sp}s;'
                    f'animation-direction:{"reverse" if rev else "normal"}">{"".join(ring)}</g></g>')
    body.append(f'<circle class="f-bg2 s-acc" cx="{cx}" cy="{cy}" r="32" stroke-width="1.5"/>'
                f'<text class="f-acc" x="{cx}" y="{cy + 6}" font-size="17" font-weight="800" text-anchor="middle">&lt;/&gt;</text>')
    y, lx = 100, 500
    for gi, grp in enumerate(groups):
        body.append(f'<g class="lg" style="animation-delay:{.3 + gi * .25:.2f}s">'
                    f'<rect class="f-{cols[gi]}" x="{lx}" y="{y - 10}" width="10" height="10" rx="2"/>'
                    f'<text class="f-ink" x="{lx + 20}" y="{y}" font-size="13.5" font-weight="700">{esc(grp["group"])}</text>')
        y += 24
        line = ""
        for it in grp["items"]:
            nxt = f"{line} · {it}" if line else it
            if len(nxt) > 40:
                body.append(f'<text class="f-dim" x="{lx + 20}" y="{y}" font-size="13">{esc(line)}</text>')
                y += 20
                nxt = it
            line = nxt
        body.append(f'<text class="f-dim" x="{lx + 20}" y="{y}" font-size="13">{esc(line)}</text></g>')
        y += 40
    label = "Tech stack. " + " ".join(f'{g["group"]}: {", ".join(g["items"])}.' for g in p["stack"])
    return svg(theme, h, label, "".join(body), css), label


# ── 6. activity: wave heatmap + odometer stats ──────────────────────────

def activity(contrib, theme):
    end = datetime.date.fromisoformat(contrib["days"][-1]["date"])
    start = end - datetime.timedelta(days=364)
    days = [d for d in contrib["days"] if d["date"] >= start.isoformat()]
    counts = sorted(d["count"] for d in days if d["count"])
    q = [counts[int(len(counts) * f)] for f in (.25, .5, .75)] if counts else [1, 2, 3]

    def lvl(c):
        return 0 if not c else 1 + sum(c > t for t in q)

    lead = (datetime.date.fromisoformat(days[0]["date"]).weekday() + 1) % 7  # Sunday-first rows
    gx, gy, step, cell = 64, 88, 14, 11
    cells, months = [], []
    for i, d in enumerate(days):
        ci, ri = divmod(i + lead, 7)
        date = datetime.date.fromisoformat(d["date"])
        if date.day == 1:
            months.append((ci, date.strftime("%b").lower()))
        glow = ' filter="url(#glow)"' if lvl(d["count"]) == 4 else ""
        cells.append(f'<rect class="f-h{lvl(d["count"])} c"{glow} x="{gx + ci * step}" y="{gy + ri * step}" '
                     f'width="{cell}" height="{cell}" rx="2" style="--k:{ci + ri}"/>')
    n_cols = (len(days) + lead + 6) // 7
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    best_m = max(monthly, key=monthly.get)
    best_label = datetime.date.fromisoformat(best_m + "-01").strftime("%b '%y").lower()
    stats = [(f"{total:,}", "contributions"), (str(active), "active days"),
             (f"{total / active:.1f}" if active else "0", "per active day"),
             (f"{monthly[best_m]:,}", f"busiest · {best_label}")]

    css = (FADE + ".c{transform-box:fill-box;transform-origin:center;"
           "animation:pop .5s cubic-bezier(.2,.8,.2,1.4) both;animation-delay:calc(var(--k) * 16ms)}"
           "@keyframes pop{from{opacity:0;transform:scale(.2)}}"
           ".od{transform:translateY(var(--y));animation:roll 1.8s cubic-bezier(.15,.8,.2,1) both}"
           "@keyframes roll{from{transform:translateY(0)}}"
           ".lb{animation:fade .6s ease both}")
    body = [""]  # frame goes here once the height is known
    for ci, m in months:
        body.append(f'<text class="f-dim" x="{gx + ci * step}" y="{gy - 8}" font-size="10.5">{m}</text>')
    for ri, wd in ((1, "mon"), (3, "wed"), (5, "fri")):
        body.append(f'<text class="f-dim" x="24" y="{gy + ri * step + 9}" font-size="10">{wd}</text>')
    body += cells
    ly = gy + 7 * step + 10
    lx = gx + n_cols * step - 5 * 14 - 34
    body.append(f'<text class="f-dim" x="{lx - 6}" y="{ly + 9}" font-size="10" text-anchor="end">less</text>')
    for k in range(5):
        body.append(f'<rect class="f-h{k}" x="{lx + k * 14}" y="{ly}" width="11" height="11" rx="2"/>')
    body.append(f'<text class="f-dim" x="{lx + 5 * 14 + 4}" y="{ly + 9}" font-size="10">more</text>')

    sy, fs, lh = ly + 70, 34, 40
    adv = fs * CW
    defs = []
    for si, (val, lab) in enumerate(stats):
        sx = gx + si * 190
        defs.append(f'<clipPath id="od{si}"><rect x="{sx - 2}" y="{sy - fs + 2}" width="{len(val) * adv + 6:.0f}" '
                    f'height="{lh}"/></clipPath>')
        digits = []
        for ci, ch in enumerate(val):
            x = sx + ci * adv
            if ch.isdigit():
                target = int(ch) + 10
                strip = "".join(f'<text x="{x:.1f}" y="{sy + j * lh}">{j % 10}</text>' for j in range(target + 1))
                digits.append(f'<g class="od" style="--y:-{target * lh}px;animation-delay:{.4 + si * .2 + ci * .08:.2f}s">'
                              f'{strip}</g>')
            else:
                digits.append(f'<text x="{x:.1f}" y="{sy}">{esc(ch)}</text>')
        body.append(f'<g class="f-ink" clip-path="url(#od{si})" font-size="{fs}" font-weight="800">{"".join(digits)}</g>'
                    f'<text class="f-dim lb" x="{sx}" y="{sy + 24}" font-size="11.5" letter-spacing="1" '
                    f'style="animation-delay:{.6 + si * .2:.1f}s">{esc(lab.upper())}</text>')
    h = sy + 52
    cards = "".join(f'<rect class="f-bg2 s-line" x="{gx - 16 + si * 190}" y="{sy - 46}" width="176" height="84" rx="12"/>'
                    for si in range(len(stats)))
    body[0] = f"<defs>{''.join(defs)}</defs>" + frame(h, "GitHub Activity", "contributions, past 12 months") + cards
    label = f"{total:,} contributions over the past 12 months across {active} active days; busiest month {best_label}."
    return svg(theme, h, label, "".join(body), css), label


# ── 7. journey: git log --graph ─────────────────────────────────────────

LANES = {"main": (44, "acc"), "feat": (72, "acc2"), "hack": (100, "acc3")}


def journey(p, theme):
    ev = p["journey"]
    top, rh = 88, 32
    n = len(ev)
    h = top + n * rh + 10
    ys = [top + i * rh for i in range(n)]
    t_of = lambda i: .3 + (n - 1 - i) * .22  # oldest (bottom) first
    css = (FADE + POP + ".dr{stroke-dasharray:1;animation:dr 2.4s ease-in-out both}"
           "@keyframes dr{from{stroke-dashoffset:1}}"
           ".rw{animation:rw .5s ease both}@keyframes rw{from{opacity:0;transform:translateX(-8px)}}")
    mx = LANES["main"][0]
    body = [frame(h, "My Journey", "git log --graph --oneline"),
            f'<path class="s-acc dr" d="M{mx},{ys[-1]} L{mx},{ys[0]}" pathLength="1" fill="none" stroke-width="2"/>']
    for i, e in enumerate(ev):
        x, col = LANES.get(e["lane"], LANES["main"])
        y = ys[i]
        if x != mx:
            body.append(f'<path class="s-{col} dr" pathLength="1" fill="none" stroke-width="2" '
                        f'style="animation-delay:{t_of(i) - .2:.2f}s;animation-duration:.6s" '
                        f'd="M{mx},{y + 16} C{x},{y + 16} {x},{y + 8} {x},{y} C{x},{y - 8} {x},{y - 16} {mx},{y - 16}"/>')
        body.append(f'<circle class="f-{col} s-bg pop" filter="url(#glow)" cx="{x}" cy="{y}" r="5.5" stroke-width="2.5" '
                    f'style="animation-delay:{t_of(i):.2f}s"/>')
        sha = hashlib.sha1(f'{e["date"]}{e["title"]}'.encode()).hexdigest()[:7]
        head = '<tspan class="f-acc">(HEAD → main) </tspan>' if i == 0 else ""
        tag = "" if e["lane"] == "main" else f'<tspan class="f-{col}">[{esc(e["lane"])}] </tspan>'
        body.append(f'<text class="rw" x="130" y="{y + 4.5}" font-size="13" style="animation-delay:{t_of(i):.2f}s">'
                    f'<tspan class="f-dim">{sha}  {esc(e["date"])}  </tspan>{head}{tag}'
                    f'<tspan class="f-ink" font-weight="700">{esc(e["title"])}</tspan>'
                    f'<tspan class="f-dim"> — {esc(e["detail"])}</tspan></text>')
    label = "Timeline, newest first: " + "; ".join(f'{e["date"]} {e["title"]} ({e["detail"]})' for e in ev) + "."
    return svg(theme, h, label, "".join(body), css), label


# ── README ──────────────────────────────────────────────────────────────

def readme(p, labels, prefix):
    img = lambda name: f'<img src="{prefix}{name}.svg" width="860" alt="{esc(labels[name])}" />'
    proj_rows = "\n".join(f'| {x["name"]} | {x["tagline"]} | {", ".join(x["stack"])} | {x["status"]} |'
                          for x in p["projects"])
    stack_rows = "\n".join(f'- **{g["group"]}:** {", ".join(g["items"])}' for g in p["stack"])
    ach = ""
    if p.get("achievements"):
        ach = "\n### Achievements\n\n" + "\n".join(f"- {a}" for a in p["achievements"]) + "\n"
    now = " · ".join(p["now"])
    return f"""<!-- Generated by scripts/render_profile.py from data/profile.json. Edit that file, not this one. -->

<div align="center">

{img("banner")}

**{p["name"]}** — {p["headline"]} · {p["education"]} · {p["location"]}<br>
Open to **{p["open_to"]}** · now {now}

{img("hero")}

{img("projects")}

{img("flagship")}

{img("stack")}

{img("activity")}

{img("journey")}

</div>
{ach}
<details>
<summary>Text version</summary>

### Projects

| Project | What it is | Stack | Status |
| --- | --- | --- | --- |
{proj_rows}

### Stack

{stack_rows}

</details>
"""


PANELS = {"banner": banner, "hero": hero, "projects": projects, "flagship": flagship,
          "stack": stack, "journey": journey}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme")
    ap.add_argument("--out", help="write SVGs + README here instead of assets/ and the repo root")
    args = ap.parse_args()
    p = load("data/profile.json")
    contrib = load("data/contributions.json")
    theme = args.theme.split(",") if args.theme else p["theme"]
    theme = [theme] if isinstance(theme, str) else theme
    bad = [t for t in theme if t not in th.THEMES]
    if bad:
        raise SystemExit(f"unknown theme {bad}; pick from: {', '.join(th.THEMES)}")
    out = os.path.join(ROOT, args.out) if args.out else os.path.join(ROOT, "assets")
    os.makedirs(out, exist_ok=True)
    labels = {}
    jobs = {**{k: (lambda f=f: f(p, theme)) for k, f in PANELS.items()},
            "activity": lambda: activity(contrib, theme)}
    for name, job in jobs.items():
        doc, labels[name] = job()
        with open(os.path.join(out, f"{name}.svg"), "w", encoding="utf-8", newline="\n") as f:
            f.write(doc)
        print(f"  {name}.svg  {len(doc) / 1024:.1f} KB")
    md_path = os.path.join(out, "README.md") if args.out else os.path.join(ROOT, "README.md")
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(readme(p, labels, "" if args.out else "assets/"))
    print(f"theme {theme}: wrote {out} + {md_path}")


if __name__ == "__main__":
    main()
