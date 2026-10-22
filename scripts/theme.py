"""Palettes shared by every generated panel. Pick one with "theme" in
data/profile.json (or `render_profile.py --theme NAME`).

Each theme has a dark and a light variant. The SVGs carry both and switch
with prefers-color-scheme, so one file works in GitHub's dark and light modes.

Tokens: bg (panel), bg2 (raised), line (borders), ink (text), dim (muted text),
acc / acc2 / acc3 (accents), h0..h4 (heatmap ramp, empty -> busiest).
"""

TOKENS = ("bg", "bg2", "line", "ink", "dim", "acc", "acc2", "acc3",
          "h0", "h1", "h2", "h3", "h4")

FONT = 'ui-monospace,"SFMono-Regular","JetBrains Mono",Menlo,Consolas,monospace'

THEMES = {
    "kanchipuram": {
        "label": "Kanchipuram Silk",
        "note": "temple gold, peacock green and kumkum red on maroon-black",
        "dark":  "#170b0e #231217 #4a2a22 #f5ead6 #b29a82 #e0a73a #2fa38a #e05a48 "
                 "#2a171b #5c3a1c #8f6224 #c48a2c #f0be4a",
        "light": "#fbf6ea #f3eadb #dccbb0 #2b1410 #7a5f4c #a8740f #0f6b5c #b3261e "
                 "#efe5d3 #e8cf93 #d6a94a #b07d1c #7a520c",
    },
    "amber": {
        "label": "Phosphor Amber",
        "note": "a 1980s amber CRT terminal: one warm hue, many brightnesses",
        "dark":  "#120d05 #1b1408 #3d2c10 #ffcf7a #a07a3a #ffb000 #ff7a1a #fff1cc "
                 "#1f170a #4a3410 #80571a #c08420 #ffb000",
        "light": "#fbf4e6 #f3e8d2 #dfc9a0 #3a2600 #85683a #b36b00 #c2410c #5c3d00 "
                 "#efe3cb #e9c98a #d9a347 #b8781a #7d4e05",
    },
    "blueprint": {
        "label": "Blueprint",
        "note": "engineering drawing: cyanotype blue, chalk white, safety orange",
        "dark":  "#0b2545 #0f2d52 #2c5282 #eef4ed #8da9c4 #f26419 #9ed0ff #f6c453 "
                 "#12305a #2a5a8c #5b8fc0 #9ec3e6 #eef4ed",
        "light": "#f4f1e8 #ebe6d8 #c9c2ad #13315c #5d6f86 #d1490b #1f5fa8 #a37b00 "
                 "#e6e1d2 #b9cbe0 #7fa3cc #3f73ad #13315c",
    },
    "kodachrome": {
        "label": "Kodachrome",
        "note": "1970s slide film: mustard, brick red and faded sky on cream",
        "dark":  "#14191a #1b2223 #34403f #f2e8d5 #9a9a8c #e0a526 #e0573f #6fb0c4 "
                 "#1e2526 #3d4a3a #7a7a33 #b88f2a #e0a526",
        "light": "#f6efe0 #ede3cf #d6c8ac #1f2324 #6b6a5e #a6700c #b33a26 #2f6f82 "
                 "#ebe2cd #d9c88f #c2a14a #9a7417 #5e4507",
    },
    "riso": {
        "label": "Neon Sakura",
        "note": "hot-pink neon and cherry blossom on midnight navy",
        "dark":  "#0f1424 #171d33 #283050 #f4f1f8 #8e93b0 #ff3d8b #ff7ab6 #ffc2dc "
                 "#1a2038 #4a1d3d #8a2457 #d1306f #ff3d8b",
        "light": "#fff6f9 #ffeaf2 #f5c9d9 #1b1530 #7a6a80 #e01e6f #c2185b #d4688f "
                 "#fbe8ef #f7bcd2 #ef86ae #e0507f #c2185b",
    },
    "sumi": {
        "label": "Sumi & Matcha",
        "note": "ink-wash black, washi paper, matcha green and a vermilion seal",
        "dark":  "#141517 #1b1d1f #34373a #ece5d8 #8f8a80 #9bb068 #e0553a #c9b27c "
                 "#1f2123 #3a4630 #5b7040 #7f9a55 #a9c272",
        "light": "#f3eee3 #e9e2d3 #d3cab8 #16181a #6e6a62 #5d7a2e #b8341b #8a6d2b "
                 "#e6dfd0 #c9d3a8 #9fb571 #6f8c3e #425a1d",
    },
}


def _vars(spec):
    return ";".join(f"--{k}:{v}" for k, v in zip(TOKENS, spec.split()))


HOLD, FADE = 9.0, 1.4  # seconds each theme shows / seconds the colour morph takes


def keyframes(n, name, states):
    """Hold each of n states, morph to the next, loop. `states` are CSS bodies."""
    seg, f = 100 / n, FADE / (n * (HOLD + FADE)) * 100
    frames = "".join(f"{i * seg:.2f}%,{(i + 1) * seg - f:.2f}%{{{s}}}" for i, s in enumerate(states))
    return f"@keyframes {name}{{{frames}100%{{{states[0]}}}}}"


def cycle_seconds(n):
    return n * (HOLD + FADE)


def css(names):
    """Palette variables (dark default, light override), one fill/stroke class
    per token, and a reduced-motion kill switch. Several names -> the palette
    morphs between them on a loop (registered @property colours interpolate)."""
    names = [names] if isinstance(names, str) else names
    first = THEMES[names[0]]
    out = (f"svg{{{_vars(first['dark'])};font-family:{FONT}}}"
           f"@media (prefers-color-scheme:light){{svg{{{_vars(first['light'])}}}}}")
    if len(names) > 1:
        n = len(names)
        out += "".join(f"@property --{k}{{syntax:'<color>';inherits:true;initial-value:#000}}" for k in TOKENS)
        out += keyframes(n, "thd", [_vars(THEMES[x]["dark"]) for x in names])
        out += keyframes(n, "thl", [_vars(THEMES[x]["light"]) for x in names])
        out += (f"svg{{animation:thd {cycle_seconds(n)}s ease-in-out infinite}}"
                "@media (prefers-color-scheme:light){svg{animation-name:thl}}")
    classes = "".join(f".f-{k}{{fill:var(--{k})}}.s-{k}{{stroke:var(--{k})}}" for k in TOKENS)
    return out + classes + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


if __name__ == "__main__":
    for name, t in THEMES.items():
        for mode in ("dark", "light"):
            assert len(t[mode].split()) == len(TOKENS), (name, mode)
    assert "--acc:#e0a73a" in css("kanchipuram")
    assert "@property" not in css("riso") and "@keyframes thl" in css(["riso", "sumi"])
    print("ok:", ", ".join(THEMES))
