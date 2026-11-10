#!/usr/bin/env python3
"""Generate a throw-away demo series (placeholder art + synthetic 'speech') to test the pipeline.

Writes demo/series and demo/episodes/demo-001. Replace with real art in series/ for production.
"""
import json
import math
import os
import wave

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "demo")
CW, CH = 500, 800
OUT = (20, 20, 20, 255)


def layer():
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def make_character(cid, shirt, hat):
    d = os.path.join(ROOT, "series", "characters", cid)
    os.makedirs(d, exist_ok=True)
    skin = (255, 214, 170, 255)
    # body + head + legs (no eyes / mouth / arms)
    im, g = layer()
    g.rectangle((205, 600, 245, 770), fill=(70, 70, 120, 255), outline=OUT, width=6)
    g.rectangle((255, 600, 295, 770), fill=(70, 70, 120, 255), outline=OUT, width=6)
    g.ellipse((190, 755, 255, 790), fill=(60, 40, 30, 255), outline=OUT, width=5)
    g.ellipse((250, 755, 315, 790), fill=(60, 40, 30, 255), outline=OUT, width=5)
    g.rounded_rectangle((165, 300, 335, 620), 40, fill=shirt, outline=OUT, width=7)
    g.ellipse((135, 70, 365, 330), fill=skin, outline=OUT, width=7)
    if hat:
        g.pieslice((130, 40, 370, 260), 180, 360, fill=hat, outline=OUT, width=7)
    im.save(os.path.join(d, "body.png"))
    # eyes (two dots) + closed
    im, g = layer()
    for x in (215, 285):
        g.ellipse((x - 11, 190, x + 11, 212), fill=OUT)
    im.save(os.path.join(d, "eyes_open.png"))
    im, g = layer()
    for x in (215, 285):
        g.line((x - 12, 204, x + 12, 204), fill=OUT, width=6)
    im.save(os.path.join(d, "eyes_closed.png"))
    # mouths
    im, g = layer()
    g.arc((215, 232, 285, 272), 20, 160, fill=OUT, width=6)
    im.save(os.path.join(d, "mouth_closed.png"))
    im, g = layer()
    g.ellipse((228, 238, 272, 266), fill=(120, 30, 40, 255), outline=OUT, width=5)
    im.save(os.path.join(d, "mouth_half.png"))
    im, g = layer()
    g.ellipse((220, 232, 280, 285), fill=(120, 30, 40, 255), outline=OUT, width=6)
    im.save(os.path.join(d, "mouth_open.png"))
    # arms hanging down from the shoulders (pivot = shoulder)
    for name, sx in (("arm_left", 170), ("arm_right", 330)):
        im, g = layer()
        g.rounded_rectangle((sx - 22, 315, sx + 22, 520), 20, fill=shirt, outline=OUT, width=6)
        g.ellipse((sx - 26, 500, sx + 26, 552), fill=skin, outline=OUT, width=6)
        im.save(os.path.join(d, name + ".png"))
    cfg = {
        "name": cid, "canvas": [CW, CH], "height_ratio": 0.62, "feet": [250, 788],
        "layers": [
            {"role": "arm", "id": "left", "image": "arm_left.png", "pivot": [170, 330], "up": -150, "point": -95},
            {"role": "static", "image": "body.png"},
            {"role": "eyes", "open": "eyes_open.png", "closed": "eyes_closed.png"},
            {"role": "mouth", "closed": "mouth_closed.png", "half": "mouth_half.png", "open": "mouth_open.png"},
            {"role": "arm", "id": "right", "image": "arm_right.png", "pivot": [330, 330],
             "up": 150, "point": 95, "main": True},
        ],
    }
    with open(os.path.join(d, "character.json"), "w") as f:
        json.dump(cfg, f, indent=2)


def make_background(name, sky, ground, blocks):
    W, H = 1920, 1080
    im = Image.new("RGB", (W, H), sky)
    g = ImageDraw.Draw(im)
    for y in range(0, 700, 4):
        c = tuple(int(sky[i] + (255 - sky[i]) * y / 900) for i in range(3))
        g.rectangle((0, y, W, y + 4), fill=c)
    g.rectangle((0, 700, W, H), fill=ground)
    for (x, w, h, col) in blocks:
        g.rectangle((x, 700 - h, x + w, 700), fill=col, outline=(30, 30, 30), width=5)
        for wy in range(700 - h + 40, 650, 90):
            for wx in range(x + 25, x + w - 40, 80):
                g.rectangle((wx, wy, wx + 40, wy + 50), fill=(250, 235, 160))
    d = os.path.join(ROOT, "series", "backgrounds")
    os.makedirs(d, exist_ok=True)
    im.save(os.path.join(d, name + ".png"))


def speech(path, dur, seed, f0):
    sr = 22050
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * sr)) / sr
    env = np.zeros_like(t)
    pos = 0.0
    while pos < dur:
        syl = rng.uniform(0.12, 0.26)
        env += np.where((t >= pos) & (t < pos + syl), np.sin(np.pi * (t - pos) / syl) ** 2, 0)
        pos += syl + rng.uniform(0.02, 0.12)
    sig = sum(math.sin(1) * np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 6))
    x = (sig * env * 0.35).astype(np.float32)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    make_character("ahmed", (240, 140, 40, 255), (230, 90, 30, 255))
    make_character("mona", (240, 110, 170, 255), None)
    make_background("street", (120, 190, 240), (200, 170, 120),
                    [(60, 380, 420, (210, 150, 110)), (520, 300, 330, (180, 200, 160)),
                     (1350, 450, 480, (200, 130, 120))])
    make_background("yard", (150, 210, 250), (110, 180, 90),
                    [(1300, 420, 300, (230, 200, 120)), (100, 300, 220, (190, 160, 210))])
    with open(os.path.join(ROOT, "series", "series.json"), "w") as f:
        json.dump({"name": "demo", "width": 1280, "height": 720, "fps": 24}, f, indent=2)

    ep = os.path.join(ROOT, "episodes", "demo-001")
    os.makedirs(os.path.join(ep, "audio"), exist_ok=True)
    L = [
        (1, "ahmed", "أهلاً يا منى! تعالي نلعب في الشارع", 3.2, 140, "raise"),
        (2, "mona", "مش هينفع يا أحمد، لازم أخلص الواجب الأول", 3.6, 210, "none"),
        (3, "ahmed", "طيب هستناكي هنا لحد ما تخلصي", 2.6, 140, "point"),
        (4, "mona", "تمام، هرجعلك بسرعة!", 2.0, 210, "wave"),
        (5, "ahmed", "يلا نروح الحديقة", 1.8, 140, "raise"),
        (6, "mona", "حلو قوي، يلا بينا", 1.8, 210, "none"),
    ]
    for lid, _, _, dur, f0, _ in L:
        speech(os.path.join(ep, "audio", f"{lid:03d}.wav"), dur, lid, f0)

    def line(i):
        lid, spk, text, _, _, gest = L[i]
        return {"id": lid, "speaker": spk, "text": text, "gesture": gest}

    scene = {"title": "demo", "shots": [
        {"background": "street", "camera": {"move": "push_in", "zoom": 1.15}, "transition": "fade",
         "characters": [{"id": "ahmed", "pos": [0.3, 0.97], "enter": "left"},
                        {"id": "mona", "pos": [0.7, 0.97], "flip": True}],
         "lines": [line(0), line(1)]},
        {"background": "street", "camera": {"move": "pan_right", "zoom": 1.12},
         "characters": [{"id": "ahmed", "pos": [0.35, 0.97]},
                        {"id": "mona", "pos": [0.75, 0.97], "flip": True}],
         "lines": [line(2), {**line(3), "move_to": [0.9, 0.97]}], "shake": {"at": 2.8, "dur": 0.4}},
        {"background": "yard", "camera": {"move": "pull_out", "zoom": 1.12}, "transition": "fade",
         "characters": [{"id": "ahmed", "pos": [0.35, 0.97], "enter": "left"},
                        {"id": "mona", "pos": [0.65, 0.97], "flip": True, "enter": "right"}],
         "lines": [line(4), line(5)]},
    ]}
    with open(os.path.join(ep, "scene.json"), "w", encoding="utf-8") as f:
        json.dump(scene, f, ensure_ascii=False, indent=2)
    print("demo written to", os.path.abspath(ROOT))


if __name__ == "__main__":
    main()
