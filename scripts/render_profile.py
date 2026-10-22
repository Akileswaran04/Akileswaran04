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
            f"<style><![CDATA[{th.css(theme)}{css}]]></style>{body}</svg>")


def frame(h, path):
    """Panel background, a path-style title and three accent squares."""
    squares = "".join(f'<rect class="f-{c}" x="{W - 58 + i * 14}" y="13" width="8" height="8" rx="1.5"/>'
                      for i, c in enumerate(("acc", "acc2", "acc3")))
    return (f'<rect class="f-bg s-line" x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="10"/>'
            f'<text class="f-dim" x="20" y="22" font-size="11.5">{esc(path)}</text>{squares}'
            f'<line class="s-line" x1="0" y1="34" x2="{W}" y2="34"/>')


RISE = "@keyframes rise{from{opacity:0;transform:translateY(10px)}}"
FADE = "@keyframes fade{from{opacity:0}}"
BLINK = "@keyframes blink{50%{opacity:0}}"
POP = ".pop{transform-box:fill-box;transform-origin:center;animation:pop .45s cubic-bezier(.2,.8,.2,1.3) both}" \
      "@keyframes pop{from{opacity:0;transform:scale(.2)}}"


# ── 1. banner: glitch name + headline + now ──────────────────────────────

def banner(p, theme):
    h = 200
    perim = 2 * (W + h)
    name = p["name"].upper()
    css = (RISE + FADE + BLINK +
           ".nm{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}"
           ".fd{animation:fade .8s ease both}"
           ".gl{opacity:0;animation:gl 7s steps(1) 1.6s infinite}"
           ".gl2{animation-delay:1.66s}"
           "@keyframes gl{0%,88%,100%{opacity:0;transform:none}89%{opacity:.9;transform:translate(-5px,2px)}"
           "91%{opacity:.9;transform:translate(4px,-2px)}93%{opacity:.9;transform:translate(-2px,0)}95%{opacity:0}}"
           ".jit{animation:jit 7s steps(1) 1.6s infinite}"
           "@keyframes jit{0%,88%,100%{transform:none}89%{transform:translateX(3px)}91%{transform:translateX(-2px)}}"
           f".trace{{stroke-dasharray:180 {perim};animation:trace 10s linear infinite}}"
           f"@keyframes trace{{from{{stroke-dashoffset:0}}to{{stroke-dashoffset:-{perim + 180}}}}}"
           ".caret{animation:blink 1s steps(1) infinite}")
    big = 'font-size="56" font-weight="800" letter-spacing="5" text-anchor="middle"'
    now = p["now"][0]
    body = (
        '<defs><pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect class="f-line" width="4" height="1" opacity=".35"/></pattern></defs>'
        f'<rect class="f-bg s-line" x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="10"/>'
        f'<rect width="{W}" height="{h}" rx="10" fill="url(#scan)"/>'
        f'<rect class="s-acc trace" x="1" y="1" width="{W - 2}" height="{h - 2}" rx="10" fill="none" stroke-width="2"/>'
        f'<text class="f-dim" x="22" y="28" font-size="11.5">~/{esc(p["handle"])}</text>'
        f'<text class="f-dim" x="{W - 22}" y="28" font-size="11.5" text-anchor="end">{esc(p["location"].lower())}</text>'
        '<g class="nm">'
        f'<text class="f-acc2 gl" x="{W / 2}" y="100" {big}>{esc(name)}</text>'
        f'<text class="f-acc3 gl gl2" x="{W / 2}" y="100" {big}>{esc(name)}</text>'
        f'<text class="f-ink jit" x="{W / 2}" y="100" {big}>{esc(name)}</text></g>'
        f'<text class="f-acc fd" x="{W / 2}" y="134" font-size="16" text-anchor="middle" '
        f'style="animation-delay:.5s">{esc(p["headline"])}</text>'
        f'<text class="fd" x="{W / 2}" y="168" font-size="13.5" text-anchor="middle" style="animation-delay:.9s">'
        f'<tspan class="f-acc2">●</tspan><tspan class="f-ink"> open to {esc(p["open_to"])}</tspan>'
        f'<tspan class="f-dim">   ·   </tspan><tspan class="f-acc">▸</tspan>'
        f'<tspan class="f-ink"> now {esc(now)}</tspan></text>'
    )
    names = [theme] if isinstance(theme, str) else theme
    if len(names) > 1:  # a toggle that flips in sync with the palette morph
        kw, sw = 64, 64 * len(names)
        x0 = W / 2 - sw / 2
        n = len(names)
        f = th.FADE / th.cycle_seconds(n)
        times, vals = [], []
        for i in range(n):
            times += [i / n, (i + 1) / n - f]
            vals += [f"{i * kw},0"] * 2
        times.append(1)
        vals.append("0,0")
        knob = (f'<animateTransform attributeName="transform" type="translate" values="{";".join(vals)}" '
                f'keyTimes="{";".join(f"{t:.4f}" for t in times)}" dur="{th.cycle_seconds(n)}s" '
                f'repeatCount="indefinite"/>')
        body += (f'<text class="f-dim" x="{x0 - 10}" y="28" font-size="13" text-anchor="end">◐</text>'
                 f'<rect class="f-bg2 s-line" x="{x0}" y="12" width="{sw}" height="22" rx="11"/>'
                 f'<rect class="f-acc" x="{x0 + 2}" y="14" width="{kw - 4}" height="18" rx="9" opacity=".4">{knob}</rect>'
                 + "".join(f'<text class="f-ink" x="{x0 + kw * i + kw / 2}" y="27" font-size="11.5" '
                           f'text-anchor="middle">{esc(nm)}</text>' for i, nm in enumerate(names)))
    label = f'{p["name"]}: {p["headline"]}. Open to {p["open_to"]}. Now {now}.'
    return svg(theme, h, label, body, css), label


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
    px, top, pw = 24, 52, 330
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
            f'<text class="f-ink pr" x="{px}" y="{y:.1f}" {tl} style="animation-delay:{d:.2f}s">{esc(r)}</text>')
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
           ".caret{animation:blink 1s steps(1) infinite}")
    body = (frame(h, f"~/{p['handle']} — whoami") + "".join(art) + beam +
            f'<line class="s-line" x1="{tx - 18}" y1="{top + 8}" x2="{tx - 18}" y2="{h - 22}" stroke-dasharray="2 4"/>' +
            "".join(out))
    label = (f"ASCII portrait of {p['name']} beside a terminal: {p['headline']}; {p['education']}; "
             f"{p['location']}; open to {p['open_to']}.")
    return svg(theme, h, label, body, css), label


# ── 3. projects: carousel with a build pipeline per project ──────────────

STAGES = ("plan", "build", "test", "ship")
STATUS = {"live": ("acc2", "● live"), "building": ("acc", "◐ building"),
          "shipped": ("acc3", "✓ shipped"), "archived": ("dim", "▣ archived")}


def projects(p, theme):
    h, per = 300, 4.5
    items = p["projects"]
    n = len(items)
    cyc = per * n
    a, b, c = 2.0, 100 / n - 2.0, 100 / n
    css = (f".sl{{animation:sl {cyc}s infinite}}"
           f"@keyframes sl{{0%{{opacity:0;transform:translateX(20px)}}{a}%{{opacity:1;transform:none}}"
           f"{b}%{{opacity:1;transform:none}}{c}%{{opacity:0;transform:translateX(-20px)}}100%{{opacity:0}}}}"
           f".st{{animation:st {cyc}s infinite}}"
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
                g.append(f'<circle class="s-acc pl" cx="{x}" cy="{sy}" r="8" fill="none" stroke-width="2"/>'
                         f'<circle class="f-acc" cx="{x}" cy="{sy}" r="5"/>')
            g.append(f'<text class="f-{"ink" if done or cur else "dim"}" x="{x}" y="{sy + 30}" font-size="12" '
                     f'text-anchor="middle">{name}</text>')
        slides.append(f'<g class="sl s{i}" style="animation-delay:{d0}s">{"".join(g)}</g>')
    dots = []
    for i in range(n):
        x = W / 2 + (i - (n - 1) / 2) * 18
        dots.append(f'<circle class="f-line" cx="{x}" cy="{h - 22}" r="4"/>'
                    f'<circle class="f-acc st dt d{i}" cx="{x}" cy="{h - 22}" r="4" style="animation-delay:{i * per}s"/>')
    body = frame(h, "~/projects — ls --pipeline") + "".join(slides) + "".join(dots)
    label = "Projects: " + "; ".join(f'{x["name"]}, {x["tagline"]} ({x["status"]})' for x in items) + "."
    return svg(theme, h, label, body, css), label


# ── 4. flagship: animated architecture flow ─────────────────────────────

def flagship(p, theme):
    f = p["flagship"]
    pr = next(x for x in p["projects"] if x["name"] == f["project"])
    nodes = f["flow"]
    h, bw, bh, yc = 240, 150, 64, 160
    n = len(nodes)
    gap = (W - 80 - n * bw) / max(n - 1, 1)
    xs = [40 + i * (bw + gap) for i in range(n)]
    col, stat = STATUS.get(pr["status"], ("dim", pr["status"]))
    css = (RISE + ".nd{animation:rise .6s cubic-bezier(.2,.8,.2,1) both}"
           ".fl{stroke-dasharray:3 7;animation:fl .8s linear infinite}@keyframes fl{to{stroke-dashoffset:-10}}")
    body = [frame(h, f"~/flagship — {f['project'].lower()} --arch"),
            f'<text class="f-ink" x="40" y="76" font-size="24" font-weight="800">{esc(pr["name"])}</text>',
            f'<text class="f-dim" x="40" y="100" font-size="14">{esc(pr["tagline"])}</text>',
            f'<text class="f-{col}" x="{W - 40}" y="76" font-size="13.5" text-anchor="end">{esc(stat)}</text>']
    for i in range(n - 1):
        x1, x2 = xs[i] + bw, xs[i + 1]
        body.append(f'<line class="s-line" x1="{x1}" y1="{yc}" x2="{x2}" y2="{yc}" stroke-width="2"/>'
                    f'<line class="s-acc fl" x1="{x1}" y1="{yc}" x2="{x2}" y2="{yc}" stroke-width="2"/>')
    path = f"M{xs[0] + bw / 2},{yc} L{xs[-1] + bw / 2},{yc}"
    for k in range(3):  # packets travel under the boxes, so they look like they pass through each stage
        body.append(f'<circle class="f-acc" r="4"><animateMotion path="{path}" dur="4.5s" '
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
    h, cx, cy = 420, 230, 225
    radii, speeds, cols = (64, 114, 164), (40, 60, 90), ("acc", "acc2", "acc3")
    css = (FADE + ".r{animation:spin linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"
           ".lg{animation:fade .6s ease both}")
    body = [frame(h, "~/stack — orbit")]
    for gi, grp in enumerate(p["stack"][:3]):
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
    y = 92
    for gi, grp in enumerate(p["stack"][:3]):
        body.append(f'<g class="lg" style="animation-delay:{.3 + gi * .25:.2f}s">'
                    f'<rect class="f-{cols[gi]}" x="470" y="{y - 10}" width="10" height="10" rx="2"/>'
                    f'<text class="f-ink" x="490" y="{y}" font-size="13.5" font-weight="700">{esc(grp["group"])}</text>')
        y += 24
        line = ""
        for it in grp["items"]:
            nxt = f"{line} · {it}" if line else it
            if len(nxt) > 44:
                body.append(f'<text class="f-dim" x="490" y="{y}" font-size="13">{esc(line)}</text>')
                y += 20
                nxt = it
            line = nxt
        body.append(f'<text class="f-dim" x="490" y="{y}" font-size="13">{esc(line)}</text></g>')
        y += 42
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
    gx, gy, step, cell = 64, 74, 14, 11
    cells, months = [], []
    for i, d in enumerate(days):
        ci, ri = divmod(i + lead, 7)
        date = datetime.date.fromisoformat(d["date"])
        if date.day == 1:
            months.append((ci, date.strftime("%b").lower()))
        cells.append(f'<rect class="f-h{lvl(d["count"])} c" x="{gx + ci * step}" y="{gy + ri * step}" '
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
    body = [frame(1, "")]  # placeholder, replaced below once height is known
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
    h = sy + 50
    body[0] = f"<defs>{''.join(defs)}</defs>" + frame(h, "~/activity — past 12 months")
    label = f"{total:,} contributions over the past 12 months across {active} active days; busiest month {best_label}."
    return svg(theme, h, label, "".join(body), css), label


# ── 7. journey: git log --graph ─────────────────────────────────────────

LANES = {"main": (44, "acc"), "feat": (72, "acc2"), "hack": (100, "acc3")}


def journey(p, theme):
    ev = p["journey"]
    top, rh = 70, 32
    n = len(ev)
    h = top + n * rh + 10
    ys = [top + i * rh for i in range(n)]
    t_of = lambda i: .3 + (n - 1 - i) * .22  # oldest (bottom) first
    css = (FADE + POP + ".dr{stroke-dasharray:1;animation:dr 2.4s ease-in-out both}"
           "@keyframes dr{from{stroke-dashoffset:1}}"
           ".rw{animation:rw .5s ease both}@keyframes rw{from{opacity:0;transform:translateX(-8px)}}")
    mx = LANES["main"][0]
    body = [frame(h, "~/journey — git log --graph --oneline"),
            f'<path class="s-acc dr" d="M{mx},{ys[-1]} L{mx},{ys[0]}" pathLength="1" fill="none" stroke-width="2"/>']
    for i, e in enumerate(ev):
        x, col = LANES.get(e["lane"], LANES["main"])
        y = ys[i]
        if x != mx:
            body.append(f'<path class="s-{col} dr" pathLength="1" fill="none" stroke-width="2" '
                        f'style="animation-delay:{t_of(i) - .2:.2f}s;animation-duration:.6s" '
                        f'd="M{mx},{y + 16} C{x},{y + 16} {x},{y + 8} {x},{y} C{x},{y - 8} {x},{y - 16} {mx},{y - 16}"/>')
        body.append(f'<circle class="f-{col} s-bg pop" cx="{x}" cy="{y}" r="5.5" stroke-width="2.5" '
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
