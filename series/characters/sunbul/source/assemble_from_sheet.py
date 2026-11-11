#!/usr/bin/env python3
"""Build the rig layers of this character from the AI parts sheet (sheet.jpg in this folder).

Run:  python3 assemble_from_sheet.py [--head-over]
Writes the layer PNGs and character.json into the parent folder (series/characters/sunbul/).
The sheet coordinates below were read from the 896x1200 sheet.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
HEAD_OVER = "--head-over" in sys.argv

# ---------- 1. remove the white background of the JPEG ----------
sheet = Image.open(os.path.join(HERE, "sheet.jpg")).convert("RGB")
A = np.array(sheet).astype(float)
lab_bg, _ = ndi.label(A.min(axis=2) >= 235)
border = set(np.unique(np.concatenate([lab_bg[0], lab_bg[-1], lab_bg[:, 0], lab_bg[:, -1]]))) - {0}
bg = np.isin(lab_bg, list(border))          # only the white connected to the border (eye whites stay)
dist = ndi.distance_transform_edt(~bg)
alpha = np.where(bg, 0.0, 1.0)
band = (~bg) & (dist <= 2.5)                 # anti-aliased edge = dark outline blended with white
alpha[band] = np.clip((255 - A.mean(axis=2)[band]) / (255 - 40), 0, 1)
rgb = A.copy()
rgb[band] = (32, 22, 20)
RGBA = np.dstack([rgb, alpha * 255]).astype(np.uint8)
lab, _ = ndi.label(ndi.binary_dilation(~bg, iterations=1))
objs = ndi.find_objects(lab)


def piece(box, tol=4):
    x0, y0, x1, y1 = box
    keep = [i + 1 for i, o in enumerate(objs)
            if o and o[1].start >= x0 - tol and o[1].stop <= x1 + tol and o[0].start >= y0 - tol and o[0].stop <= y1 + tol]
    m = np.isin(lab, keep)
    out = RGBA.copy()
    out[~m] = 0
    ys, xs = np.where(out[..., 3] > 6)
    return Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


def split_rows(im, parts=2):
    a = np.array(im)[..., 3] > 6
    rows = a.sum(axis=1)
    h = len(rows)
    cut = int(h * 0.3) + int(np.argmin(rows[int(h * 0.3):int(h * 0.7)]))
    top, bot = im.crop((0, 0, im.width, cut)), im.crop((0, cut, im.width, im.height))
    return [Image.fromarray(np.array(p)[tuple(slice(s.min(), s.max() + 1) for s in np.where(np.array(p)[..., 3] > 6))])
            for p in (top, bot)]


P = {
    "head": piece((32, 33, 285, 317)), "hair": piece((325, 38, 566, 195)),
    "torso": piece((436, 368, 651, 670)), "arm_l": piece((279, 416, 414, 679)), "arm_r": piece((678, 416, 813, 679)),
    "shorts": piece((428, 689, 659, 881)), "leg_l": piece((376, 895, 510, 1170)), "leg_r": piece((577, 895, 710, 1170)),
    "hand_a": piece((47, 332, 126, 483)), "hand_b": piece((133, 332, 212, 483)), "hand_point": piece((41, 488, 163, 548)),
    "eye_l": piece((40, 784, 87, 820)), "eye_r": piece((113, 784, 159, 820)),
    "brow_l": piece((27, 920, 86, 939)), "brow_r": piece((114, 920, 173, 939)), "nose": piece((64, 1006, 104, 1057)),
    "mouth_closed": piece((49, 1136, 119, 1151)), "mouth_half": piece((156, 1131, 190, 1161)),
    "mouth_open": piece((230, 1077, 306, 1119)),
}
P["hand_fist"], _thumb = split_rows(piece((40, 545, 159, 666)))

# ---------- 2. layout (canvas coordinates) ----------
CW, CH = 640, 1000
CX = CW // 2
HEAD_Y = 20
head_x = CX - P["head"].width // 2
torso_x, torso_y = CX - P["torso"].width // 2, HEAD_Y + P["head"].height - 40
shorts_x, shorts_y = CX - P["shorts"].width // 2, torso_y + P["torso"].height - 30


def cx_top(im, frac=0.15):
    a = np.array(im)[..., 3] > 128
    ys, xs = np.where(a[: max(2, int(a.shape[0] * frac))])
    return xs.mean()


leg_y = shorts_y + 140
leg_l_x = shorts_x + P["shorts"].width * 0.25 - cx_top(P["leg_l"])
leg_r_x = shorts_x + P["shorts"].width * 0.75 - cx_top(P["leg_r"])
# arms keep the offset they had next to the torso in the sheet, moved in so the sleeves overlap the torso
arm_l_pos = (torso_x - 120, torso_y + 48)
arm_r_pos = (torso_x + 200, torso_y + 48)


def canvas():
    return Image.new("RGBA", (CW, CH), (0, 0, 0, 0))


def put(c, im, xy):
    c.alpha_composite(im, (int(round(xy[0])), int(round(xy[1]))))


# ---------- 3. hands attached to the arm ends ----------
def arm_axis(im):
    a = np.array(im)[..., 3] > 128
    h = a.shape[0]
    ys, xs = [], []
    for y in range(int(h * 0.6), h):
        row = np.where(a[y])[0]
        if len(row):
            ys.append(y)
            xs.append(row.mean())
    slope = np.polyfit(ys, xs, 1)[0]
    return math.degrees(math.atan(slope))


def run_width(im, y0, y1):
    a = np.array(im)[..., 3] > 128
    ws = [np.ptp(np.where(a[y])[0]) + 1 for y in range(y0, y1) if a[y].any()]
    return float(np.mean(ws))


def trim_end(arm, rows=24):
    """Cut the rounded end of the arm (its outline would show as a ring on the wrist)."""
    a = np.array(arm)
    keep = np.where(a[..., 3] > 128)[0].max() - rows
    a[keep:] = 0
    a = a[: keep]
    return Image.fromarray(a), arm.height - rows


def rot_point(p, size, theta):
    """Where point p of an image of `size` ends up after PIL rotate(theta, expand=True)."""
    t = math.radians(theta)
    dx, dy = p[0] - size[0] / 2, p[1] - size[1] / 2
    nw = abs(size[0] * math.cos(t)) + abs(size[1] * math.sin(t))
    nh = abs(size[0] * math.sin(t)) + abs(size[1] * math.cos(t))
    return nw / 2 + dx * math.cos(t) + dy * math.sin(t), nh / 2 - dx * math.sin(t) + dy * math.cos(t)


def hand_on_arm(arm, hand, base_rot, mirror, overlap=12, wrist_cut=14):
    """Wrist at the top, same width as the arm, wrist outline removed, glued to the trimmed arm end."""
    theta = arm_axis(arm)
    trimmed, end_y = trim_end(arm)
    ends = np.array(trimmed)[..., 3] > 128
    ex = float(np.where(ends[-6:].any(axis=0))[0].mean())
    h = hand.rotate(base_rot, expand=True, resample=Image.BICUBIC) if base_rot else hand
    if mirror:
        h = h.transpose(Image.FLIP_LEFT_RIGHT)
    w_arm = run_width(trimmed, trimmed.height - 40, trimmed.height - 10)
    k = float(np.clip(w_arm / run_width(h, 16, 34), 0.8, 2.0))
    h = h.resize((round(h.width * k), round(h.height * k)), Image.LANCZOS)
    h = h.crop((0, wrist_cut, h.width, h.height))
    wrist = (h.width / 2, 0)
    hr = h.rotate(theta, expand=True, resample=Image.BICUBIC)
    wx, wy = rot_point(wrist, h.size, theta)
    ux, uy = math.sin(math.radians(theta)), math.cos(math.radians(theta))
    tx, ty = ex - overlap * ux, trimmed.height - overlap * uy
    return trimmed, hr, (tx - wx, ty - wy)


def arm_image(arm, pos, pose, mirror):
    hand = {"rest": (P["hand_fist"], -90, mirror), "point": (P["hand_point"], -90, mirror),
            "open": (P["hand_a" if not mirror else "hand_b"], 180, False)}[pose]
    c = canvas()
    trimmed, hr, (hx, hy) = hand_on_arm(arm, *hand)
    put(c, trimmed, pos)
    put(c, hr, (pos[0] + hx, pos[1] + hy))
    return c


# ---------- 4. face ----------
face_cx = head_x + P["head"].width / 2
EYE_Y, BROW_Y, NOSE_Y, MOUTH_Y, EYE_DX = HEAD_Y + 112, HEAD_Y + 80, HEAD_Y + 140, HEAD_Y + 172, 50


def centred(c, im, cx, cy):
    put(c, im, (cx - im.width / 2, cy - im.height / 2))


def squash(im, k=0.18):
    return im.resize((im.width, max(3, int(im.height * k))), Image.LANCZOS)


def eyes(closed):
    c = canvas()
    for im, dx in ((P["eye_l"], -EYE_DX), (P["eye_r"], EYE_DX)):
        centred(c, squash(im) if closed else im, face_cx + dx, EYE_Y)
    for im, dx in ((P["brow_l"], -EYE_DX), (P["brow_r"], EYE_DX)):
        centred(c, im, face_cx + dx, BROW_Y)
    return c


def face_piece(key, cy):
    c = canvas()
    centred(c, P[key], face_cx, cy)
    return c


# ---------- 5. layers ----------
body = canvas()
put(body, P["leg_l"], (leg_l_x, leg_y))
put(body, P["leg_r"], (leg_r_x, leg_y))
put(body, P["shorts"], (shorts_x, shorts_y))
if HEAD_OVER:
    put(body, P["torso"], (torso_x, torso_y))
    put(body, P["head"], (head_x, HEAD_Y))
else:
    put(body, P["head"], (head_x, HEAD_Y))
    put(body, P["torso"], (torso_x, torso_y))
put(body, P["hair"], (face_cx - P["hair"].width / 2, HEAD_Y - 22))

layers = {"body": body, "eyes_open": eyes(False), "eyes_closed": eyes(True),
          "mouth_closed": face_piece("mouth_closed", MOUTH_Y), "mouth_half": face_piece("mouth_half", MOUTH_Y),
          "mouth_open": face_piece("mouth_open", MOUTH_Y)}
nose = canvas()
centred(nose, P["nose"], face_cx, NOSE_Y)
layers["body"].alpha_composite(nose)

pivots = {}
for side, arm, pos, mirror in (("l", P["arm_l"], arm_l_pos, False), ("r", P["arm_r"], arm_r_pos, True)):
    for pose in ("rest", "open", "point"):
        layers[f"arm_{side}_{pose}"] = arm_image(arm, pos, pose, mirror)
    pivots[side] = [round(pos[0] + cx_top(arm, 0.05)), round(pos[1] + 38)]

for k, v in layers.items():
    v.save(os.path.join(OUT, k + ".png"))

feet = [round(CX), round(leg_y + P["leg_l"].height - 6)]
cfg = {
    "name": "sunbul", "canvas": [CW, CH], "height_ratio": 0.66, "feet": feet,
    "layers": [
        {"role": "static", "image": "body.png"},
        {"role": "eyes", "open": "eyes_open.png", "closed": "eyes_closed.png"},
        {"role": "mouth", "closed": "mouth_closed.png", "half": "mouth_half.png", "open": "mouth_open.png"},
        {"role": "arm", "id": "l", "image": "arm_l_rest.png", "pivot": pivots["l"], "up": -150, "point": -95,
         "poses": {"rest": "arm_l_rest.png", "open": "arm_l_open.png", "point": "arm_l_point.png"}},
        {"role": "arm", "id": "r", "image": "arm_r_rest.png", "pivot": pivots["r"], "up": 150, "point": 95, "main": True,
         "poses": {"rest": "arm_r_rest.png", "open": "arm_r_open.png", "point": "arm_r_point.png"}},
    ],
}
json.dump(cfg, open(os.path.join(OUT, "character.json"), "w"), indent=1)

prev = canvas()
for k in ("body", "eyes_open", "mouth_closed", "arm_l_rest", "arm_r_rest"):
    prev.alpha_composite(layers[k])
bgc = Image.new("RGBA", (CW, CH), (225, 225, 225, 255))
bgc.alpha_composite(prev)
bgc.convert("RGB").save(os.path.join(HERE, "preview.png"))
print("ok", feet, pivots)
