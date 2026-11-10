"""Cut-out character: layered PNGs (all the same canvas size) animated per frame."""
import math
import os

from PIL import Image

from scene import load_json


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def gesture_factor(t_rel, dur, ramp=0.25):
    r = min(ramp, dur / 2) if dur > 0 else 0.01
    return ease(t_rel / r) * ease((dur - t_rel) / r)


class Character:
    def __init__(self, series_dir, cid):
        self.id = cid
        self.dir = os.path.join(series_dir, "characters", cid)
        self.cfg = load_json(os.path.join(self.dir, "character.json"))
        self.cw, self.ch = self.cfg["canvas"]
        self.height_ratio = self.cfg.get("height_ratio", 0.6)
        self.feet = self.cfg.get("feet", [self.cw / 2, self.ch - 4])
        self._raw, self._scaled, self._rot = {}, {}, {}
        arms = [L for L in self.cfg["layers"] if L["role"] == "arm"]
        main = [L for L in arms if L.get("main")]
        self.main_arm = (main or arms[-1:] or [None])[0]
        self.arms = arms

    def _img(self, fn, k):
        key = (fn, round(k, 4))
        if key not in self._scaled:
            if fn not in self._raw:
                self._raw[fn] = Image.open(os.path.join(self.dir, fn)).convert("RGBA")
            im = self._raw[fn]
            size = (max(1, round(self.cw * k)), max(1, round(self.ch * k)))
            self._scaled[key] = im.resize(size, Image.LANCZOS)
        return self._scaled[key]

    def _arm_img(self, fn, k, angle, pivot):
        a = round(angle)
        key = (fn, round(k, 4), a)
        if key not in self._rot:
            im = self._img(fn, k)
            self._rot[key] = im if a == 0 else im.rotate(
                a, resample=Image.BICUBIC, center=(pivot[0] * k, pivot[1] * k))
        return self._rot[key]

    def arm_angles(self, gesture, f, t):
        """Angles (degrees, counter-clockwise positive) for every arm layer."""
        out = {}
        for L in self.arms:
            up = L.get("up", 120)
            sway = 3 * math.sin(2 * math.pi * t / 2.0 + len(L["id"]))
            ang = sway
            is_main = L is self.main_arm
            if gesture == "both_raise" or (is_main and gesture in ("raise", "point", "wave")):
                if gesture == "point":
                    ang = f * L.get("point", up * 0.65) + (1 - f) * sway
                elif gesture == "wave":
                    ang = f * (up + 18 * math.sin(2 * math.pi * 3 * t)) + (1 - f) * sway
                else:
                    ang = f * up + (1 - f) * sway
            out[L["id"]] = ang
        return out

    def sprite(self, k, mouth, blink, eye_off, angles, emotion, flip):
        W, H = round(self.cw * k), round(self.ch * k)
        base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        emo = self.cfg.get("emotions", {}).get(emotion, {})
        for L in self.cfg["layers"]:
            role = L["role"]
            if role == "static":
                base.alpha_composite(self._img(L["image"], k))
            elif role == "arm":
                fn = emo.get("arm", {}).get(L["id"], L["image"])
                base.alpha_composite(self._arm_img(fn, k, angles.get(L["id"], 0), L["pivot"]))
            elif role == "eyes":
                key = "closed" if blink and L.get("closed") else "open"
                fn = emo.get("eyes", {}).get(key, L[key])
                im = self._img(fn, k)
                dx, dy = round(eye_off[0] * k), round(eye_off[1] * k)
                if dx or dy:
                    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                    tmp.paste(im, (dx, dy))
                    im = tmp
                base.alpha_composite(im)
            elif role == "mouth":
                key = ("closed", "half", "open")[mouth]
                if key not in L:
                    key = "open" if key == "half" else "closed"
                fn = emo.get("mouth", {}).get(key, L[key])
                base.alpha_composite(self._img(fn, k))
        fx, fy = self.feet[0] * k, self.feet[1] * k
        if flip:
            base = base.transpose(Image.FLIP_LEFT_RIGHT)
            fx = W - fx
        return base, fx, fy
