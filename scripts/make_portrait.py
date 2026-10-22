"""
Convert a portrait photo into clean, monochrome ASCII art and write it to
data/portrait.txt. render_profile.py turns that text into the animated hero
panel (decrypt effect, theme colours), so this only needs re-running when the
photo changes.

  python scripts/prep_photo.py        # pic/profile.jpeg -> source-prepped.png
  python scripts/make_portrait.py     # source-prepped.png -> data/portrait.txt

Local-only: needs scripts/requirements-local.txt. Photos stay out of git.
"""
from PIL import Image, ImageEnhance, ImageFilter
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# defaults to the prepped grayscale image (see prep_photo.py), which already has
# the background removed + local contrast applied.
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "data", "portrait.txt")

COLS = 100
ROWS = 53
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg

# the prepped image already has bg removed + CLAHE local contrast, so only
# light global tuning is needed here.
CONTRAST = 1.12
BRIGHTNESS = 1.0
GAMMA = 1.28          # >1 brightens mids -> face lands in sparser chars
SHARPEN = False
WHITE_FLOOR = 0.80    # luminance above this is forced to blank (space)

im = Image.open(SRC).convert("L")               # grayscale
if SHARPEN:
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = pow(px[x, y] / 255.0, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1) + 0.5)
        chars.append(RAMP[max(0, min(len(RAMP) - 1, idx))])
    rows_txt.append("".join(chars).rstrip())

with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(rows_txt) + "\n")
print("wrote", OUT, f"({COLS}x{ROWS})")
