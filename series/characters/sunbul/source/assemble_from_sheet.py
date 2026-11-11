#!/usr/bin/env python3
"""Build the rig layers for SUNBUL (green hoodie boy).

Body parts come from sheet_parts.jpg (magenta background, 1199x896).
Eyes and mouths come from sheet_faceparts.png (transparent background) of the same character.
Writes the layer PNGs + character.json into the parent folder. Preview: source/preview.png
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
DARK = (40, 25, 20)


# ---------- keying ----------
def key_magenta(path):
    a = np.array(Image.open(path).convert("RGB")).astype(float)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    bg = (r > 170) & (b > 170) & (g < 125) & (r - g > 80) & (b - g > 80)
    dist = ndi.distance_transform_edt(~bg)
    alpha = np.where(bg, 0.0, 1.0)
    band = (~bg) & (dist <= 2.5)
    alpha[band] = np.clip((255 - r[band]) / (255 - 50), 0, 1)
    rgb = a.copy()
    rgb[band] = DARK
    return np.dstack([rgb, alpha * 255]).astype(np.uint8)


def pieces_of(rgba, dil=1):
    lab, _ = ndi.label(ndi.binary_dilation(rgba[..., 3] > 20, iterations=dil))
    return lab, ndi.find_objects(lab)


def cutter(rgba):
    lab, objs = pieces_of(rgba)

    def piece(box, tol=4):
        x0, y0, x1, y1 = box
        keep = [i + 1 for i, o in enumerate(objs) if o and o[1].start >= x0 - tol and o[1].stop <= x1 + tol
                and o[0].start >= y0 - tol and o[0].stop <= y1 + tol]
        m = np.isin(lab, keep)
        out = rgba.copy()
        out[~m] = 0
        ys, xs = np.where(out[..., 3] > 6)
        return Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    return piece


body_piece = cutter(key_magenta(os.path.join(HERE, "sheet_parts.jpg")))
_fa = np.array(Image.open(os.path.join(HERE, "sheet_faceparts.png")).convert("RGBA"))
_flab, _ = pieces_of(_fa)
_fc = ndi.center_of_mass(np.ones_like(_flab), _flab, range(1, _flab.max() + 1))


def face_piece(box):
    x0, y0, x1, y1 = box
    keep = [i + 1 for i, (cy, cx) in enumerate(_fc) if x0 <= cx <= x1 and y0 <= cy <= y1]
    m = np.isin(_flab, keep)
    out = _fa.copy()
    out[~m] = 0
    ys, xs = np.where(out[..., 3] > 6)
    return Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1])

N = {
    "head": body_piece((36, 31, 225, 242)), "hair": body_piece((239, 16, 413, 156)),
    "torso": body_piece((693, 24, 854, 261)),
    "sleeve_a": body_piece((921, 51, 1019, 171)), "arm": body_piece((1094, 197, 1149, 373)),
    "shorts_l": body_piece((679, 273, 766, 403)), "shorts_r": body_piece((782, 270, 872, 403)),
    "leg_a": body_piece((442, 735, 516, 862)), "leg_b": body_piece((547, 734, 619, 862)),
}
F = {
    "eyes_open": face_piece((518, 530, 622, 610)), "eyes_closed": face_piece((628, 535, 730, 590)),
    "mouth_closed": face_piece((535, 668, 598, 690)), "mouth_half": face_piece((515, 695, 568, 735)),
    "mouth_open": face_piece((640, 690, 718, 730)),
}


def scaled(im, k):
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


# the legs come from the smaller set on the sheet
LEG_K = 1.55
N["leg_a"], N["leg_b"] = scaled(N["leg_a"], LEG_K), scaled(N["leg_b"], LEG_K)
FACE_K = N["head"].width / 253.0          # the face parts were drawn for a 253 px wide head
F = {k: scaled(v, FACE_K) for k, v in F.items()}

CW, CH = 760, 770
CX = CW // 2


def canvas():
    return Image.new("RGBA", (CW, CH), (0, 0, 0, 0))


def put(c, im, xy):
    c.alpha_composite(im, (int(round(xy[0])), int(round(xy[1]))))


def cx_top(im, frac=0.2):
    a = np.array(im)[..., 3] > 128
    ys, xs = np.where(a[: max(2, int(a.shape[0] * frac))])
    return xs.mean()


# ---------- longer neck (the stub on the sheet is too short to reach the hood opening) ----------
def extend_neck(im, extra=46, band=6):
    a = np.array(im)
    ext = np.array(Image.fromarray(a[-band:]).resize((im.width, extra), Image.NEAREST))
    return Image.fromarray(np.concatenate([a, ext], axis=0))


HEAD0_H = N["head"].height
_w = (np.array(N["head"])[..., 3] > 128).sum(axis=1)
SKULL_H = next(i for i in range(HEAD0_H // 2, HEAD0_H) if _w[i] <= 0.4 * _w.max())
N["head"] = extend_neck(N["head"])

# ---------- layout ----------
head_w, head_h = N["head"].size
head_x, head_y = CX - head_w // 2, 18
torso_w, torso_h = N["torso"].size
torso_x, torso_y = CX - torso_w // 2, head_y + SKULL_H + 4
shorts_y = torso_y + torso_h - 28
sh_l_x, sh_r_x = CX - N["shorts_l"].width + 2, CX - 2
leg_y = shorts_y + N["shorts_l"].height - 40
leg_a_x = sh_l_x + N["shorts_l"].width / 2 - cx_top(N["leg_a"])
leg_b_x = sh_r_x + N["shorts_r"].width / 2 - cx_top(N["leg_b"])

sl_w, sl_h = N["sleeve_a"].size
arm_w, arm_h = N["arm"].size
sleeve_l_pos = (torso_x - sl_w + 30, torso_y + 16)
sleeve_r_pos = (torso_x + torso_w - 30, torso_y + 16)
arm_l_pos = (sleeve_l_pos[0] + sl_w * 0.45 - arm_w / 2, sleeve_l_pos[1] + 36)
arm_r_pos = (sleeve_r_pos[0] + sl_w * 0.55 - arm_w / 2, sleeve_r_pos[1] + 36)
pivot_l = (arm_l_pos[0] + arm_w / 2, arm_l_pos[1] + 24)
pivot_r = (arm_r_pos[0] + arm_w / 2, arm_r_pos[1] + 24)

# ---------- face ----------
face_cx = head_x + head_w / 2
EYE_Y, MOUTH_Y, NOSE_Y = head_y + round(HEAD0_H * 0.40), head_y + round(HEAD0_H * 0.62), head_y + round(HEAD0_H * 0.505)


def centred(c, im, cx, cy):
    put(c, im, (cx - im.width / 2, cy - im.height / 2))


def nose_img():
    k = 4
    im = Image.new("RGBA", (30 * k, 26 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((5 * k, 4 * k, 25 * k, 22 * k), fill=(236, 168, 128, 255))
    d.arc((5 * k, 4 * k, 25 * k, 22 * k), 20, 160, fill=DARK + (255,), width=2 * k)
    return im.resize((30, 26), Image.LANCZOS)


# ---------- layers ----------
hood = canvas()          # dark fill behind the neck, between the two hood flaps
ta = np.array(N["torso"])[..., 3] > 128
d = ImageDraw.Draw(hood)
for yy in range(0, 48):
    xs = np.where(ta[yy])[0]
    if len(xs) > 2:
        d.line((torso_x + xs.min(), torso_y + yy, torso_x + xs.max(), torso_y + yy), fill=(205, 165, 25, 255))

body = canvas()
put(body, N["leg_a"], (leg_a_x, leg_y))
put(body, N["leg_b"], (leg_b_x, leg_y))
navy = tuple(int(v) for v in np.median(np.array(N["shorts_l"])[60:100, 20:60, :3].reshape(-1, 3), axis=0)) + (255,)
ImageDraw.Draw(body).rectangle((CX - 14, shorts_y + 2, CX + 14, shorts_y + 60), fill=navy)
put(body, N["shorts_l"], (sh_l_x, shorts_y))
put(body, N["shorts_r"], (sh_r_x, shorts_y))
put(body, N["head"], (head_x, head_y))
put(body, N["torso"], (torso_x, torso_y))
hair = scaled(N["hair"], 1.1)
put(body, hair, (face_cx - hair.width / 2, head_y - 30))
centred(body, nose_img(), face_cx, NOSE_Y)


def single(im, cy):
    c = canvas()
    centred(c, im, face_cx, cy)
    return c


layers = {
    "body": body,
    "eyes_open": single(F["eyes_open"], EYE_Y), "eyes_closed": single(F["eyes_closed"], EYE_Y + 2),
    "mouth_closed": single(F["mouth_closed"], MOUTH_Y), "mouth_half": single(F["mouth_half"], MOUTH_Y),
    "mouth_open": single(F["mouth_open"], MOUTH_Y),
}
arm_l, arm_r = mirror(N["arm"]), N["arm"]
sleeve_l, sleeve_r = N["sleeve_a"], mirror(N["sleeve_a"])
for name, im, pos in (("arm_l", arm_l, arm_l_pos), ("arm_r", arm_r, arm_r_pos),
                      ("sleeve_l", sleeve_l, sleeve_l_pos), ("sleeve_r", sleeve_r, sleeve_r_pos)):
    c = canvas()
    put(c, im, pos)
    layers[name] = c

for k, v in layers.items():
    v.save(os.path.join(OUT, k + ".png"))

feet = [round(CX), round(leg_y + N["leg_a"].height - 6)]
cfg = {
    "name": "sunbul", "canvas": [CW, CH], "height_ratio": 0.66, "feet": feet,
    "layers": [
        {"role": "static", "image": "body.png"},
        {"role": "eyes", "open": "eyes_open.png", "closed": "eyes_closed.png"},
        {"role": "mouth", "closed": "mouth_closed.png", "half": "mouth_half.png", "open": "mouth_open.png"},
        {"role": "arm", "id": "l", "image": "arm_l.png", "pivot": [round(pivot_l[0]), round(pivot_l[1])],
         "up": -150, "point": -95},
        {"role": "arm", "id": "ls", "image": "sleeve_l.png", "follow": "l", "factor": 0.85,
         "pivot": [round(pivot_l[0]), round(pivot_l[1])]},
        {"role": "arm", "id": "r", "image": "arm_r.png", "pivot": [round(pivot_r[0]), round(pivot_r[1])],
         "up": 150, "point": 95, "main": True},
        {"role": "arm", "id": "rs", "image": "sleeve_r.png", "follow": "r", "factor": 0.85,
         "pivot": [round(pivot_r[0]), round(pivot_r[1])]},
    ],
}
json.dump(cfg, open(os.path.join(OUT, "character.json"), "w"), indent=1)

prev = canvas()
for k in ("body", "eyes_open", "mouth_closed", "arm_l", "sleeve_l", "arm_r", "sleeve_r"):
    prev.alpha_composite(layers[k])
bgc = Image.new("RGBA", (CW, CH), (225, 225, 225, 255))
bgc.alpha_composite(prev)
bgc.convert("RGB").save(os.path.join(HERE, "preview.png"))
print("ok feet", feet, "pivots", pivot_l, pivot_r, "head", N["head"].size, "torso", N["torso"].size)
