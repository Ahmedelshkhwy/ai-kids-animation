import os
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sheet.png")
OUT = sys.argv[1]
sheet = Image.open(SRC).convert("RGBA")
A = np.array(sheet)
lab, n = ndi.label(A[..., 3] > 20)
cent = ndi.center_of_mass(np.ones_like(lab), lab, range(1, n + 1))


def part(box):
    """Union of components whose centroid is inside box -> tight RGBA crop."""
    x0, y0, x1, y1 = box
    keep = [i + 1 for i, (cy, cx) in enumerate(cent) if x0 <= cx <= x1 and y0 <= cy <= y1]
    m = np.isin(lab, keep)
    ys, xs = np.where(m)
    out = A.copy()
    out[~m] = 0
    return Image.fromarray(out[ys.min():ys.max() + 1, xs.min():xs.max() + 1])


P = {
    "head": part((25, 525, 195, 715)),
    "hair_top": part((190, 512, 346, 640)),
    "bangs": part((212, 650, 342, 720)),
    "torso": part((45, 715, 185, 912)),
    "arm": part((200, 735, 285, 1000)),
    "eyes_open": part((518, 530, 622, 595)),
    "eyes_happy": part((628, 535, 730, 590)),
    "mouth_closed": part((535, 668, 598, 690)),
    "mouth_half": part((515, 695, 568, 735)),
    "mouth_open": part((640, 690, 718, 730)),
    "short_l": part((570, 790, 640, 890)),
    "short_r": part((645, 790, 715, 890)),
    "leg_l": part((530, 885, 630, 1045)),
    "leg_r": part((655, 885, 755, 1045)),
}


def clean_head(im):
    """Remove the baked-in eyes/brows/smile so the face layers can be swapped."""
    a = np.array(im)
    h, w = a.shape[:2]
    skin = np.median(a[int(h * .30):int(h * .36), int(w * .45):int(w * .55)][..., :3].reshape(-1, 3), axis=0)
    y0, y1, x0, x1 = int(h * .28), int(h * .74), int(w * .24), int(w * .76)
    reg = a[y0:y1, x0:x1]
    diff = np.abs(reg[..., :3].astype(int) - skin).sum(axis=2)
    mask = (diff > 60) & (reg[..., 3] > 0)
    mask = ndi.binary_dilation(mask, iterations=3)
    rgb = reg[..., :3].astype(float)
    rgb[mask] = skin
    for _ in range(300):
        blur = ndi.uniform_filter(rgb, size=(5, 5, 1))
        rgb[mask] = blur[mask]
    reg[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    a[y0:y1, x0:x1] = reg
    return Image.fromarray(a)


P["head"] = clean_head(P["head"])
for k, v in P.items():
    v.save(f"{OUT}/part_{k}.png")
    print(k, v.size)

# ---- placement v2 ----
CW, CH = 440, 630
cfg = json.load(open(f"{OUT}/place.json")) if len(sys.argv) > 2 else None
ARM_S = 0.85


def top_cx(im):
    a = np.array(im)[..., 3]
    ys, xs = np.where(a[:12] > 0)
    return xs.mean()


def scaled(im, k):
    return im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)


def cx_of(im, frac=0.2):
    a = np.array(im)[..., 3]
    ys, xs = np.where(a[: int(a.shape[0] * frac)] > 0)
    return xs.mean()


eyes = {k: scaled(P[k], 0.88) for k in ("eyes_open", "eyes_happy")}
arm = scaled(P["arm"], ARM_S)
arm_b = arm.transpose(Image.FLIP_LEFT_RIGHT)
TORSO_X, TORSO_Y = 158, 205
HEAD_X, HEAD_Y = 141, 62
SH_Y = 362
sl_x, sr_x = 156, 218
leg_l_x = sl_x + P["short_l"].width / 2 - cx_of(P["leg_l"])
leg_r_x = sr_x + P["short_r"].width / 2 - cx_of(P["leg_r"])
LEG_Y = SH_Y + 70
face_cx = HEAD_X + P["head"].width / 2
pl = {
    "leg_l": (leg_l_x, LEG_Y), "leg_r": (leg_r_x, LEG_Y),
    "short_l": (sl_x, SH_Y), "short_r": (sr_x, SH_Y),
    "head": (HEAD_X, HEAD_Y), "torso": (TORSO_X, TORSO_Y),
    "hair_top": (face_cx - P["hair_top"].width / 2, HEAD_Y - 42),
    "bangs": (face_cx - P["bangs"].width / 2, HEAD_Y - 4),
    "eyes_open": (face_cx - eyes["eyes_open"].width / 2, HEAD_Y + 58),
    "eyes_happy": (face_cx - eyes["eyes_happy"].width / 2, HEAD_Y + 62),
    "mouth_closed": (face_cx - P["mouth_closed"].width / 2, HEAD_Y + 128),
    "mouth_half": (face_cx - P["mouth_half"].width / 2, HEAD_Y + 124),
    "mouth_open": (face_cx - P["mouth_open"].width / 2, HEAD_Y + 122),
    "arm_back": (TORSO_X - arm.width * 0.65, TORSO_Y + 2),
    "arm_front": (TORSO_X + P["torso"].width - arm.width * 0.35, TORSO_Y + 2),
}
if cfg:
    pl.update({k: tuple(v) for k, v in cfg.items()})
IMG = {**P, **eyes}
IMG["arm_back"], IMG["arm_front"] = arm_b, arm


def layer(names):
    c = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    for k in names:
        c.alpha_composite(IMG[k], (round(pl[k][0]), round(pl[k][1])))
    return c


layers = {
    "arm_back": layer(["arm_back"]),
    "body": layer(["leg_l", "leg_r", "short_l", "short_r", "head", "torso", "hair_top", "bangs"]),
    "eyes_open": layer(["eyes_open"]), "eyes_closed": layer(["eyes_happy"]),
    "mouth_closed": layer(["mouth_closed"]), "mouth_half": layer(["mouth_half"]),
    "mouth_open": layer(["mouth_open"]), "arm_front": layer(["arm_front"]),
}
import os
os.makedirs(f"{OUT}/layers", exist_ok=True)
for k, v in layers.items():
    v.save(f"{OUT}/layers/{k}.png")
full = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
for k in ["arm_back", "body", "eyes_open", "mouth_closed", "arm_front"]:
    full.alpha_composite(layers[k])
bg = Image.new("RGBA", (CW * 2 + 20, CH), (225, 225, 225, 255))
bg.alpha_composite(full, (0, 0))
bg.alpha_composite(sheet.crop((245, 0, 415, 500)).resize((212, 625), Image.LANCZOS), (CW + 20, 0))
bg.convert("RGB").save(f"{OUT}/preview.png")
sh_y = TORSO_Y + 2 + 24
pivots = {"arm_back": [round(pl["arm_back"][0] + top_cx(arm_b)), round(sh_y)],
          "arm_front": [round(pl["arm_front"][0] + top_cx(arm)), round(sh_y)]}
feet_y = round(LEG_Y + max(P["leg_l"].height, P["leg_r"].height) - 3)
meta = {"pivots": pivots, "feet": [round(face_cx), feet_y]}
json.dump(meta, open(f"{OUT}/meta.json", "w"))
print(meta, "canvas", CW, CH)
