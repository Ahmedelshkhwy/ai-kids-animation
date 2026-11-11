"""Frame renderer: background + cut-out characters + camera + subtitles -> mp4."""
import math
import os
import subprocess
import zlib
from multiprocessing import Pool

import numpy as np
from PIL import Image

import audio
import subtitles
from rig import Character, ease, gesture_factor
from scene import find_background

_chars = {}


def _char(series_dir, cid):
    key = (series_dir, cid)
    if key not in _chars:
        _chars[key] = Character(series_dir, cid)
    return _chars[key]


def _camera(shot, t, length):
    cam = shot.get("camera", {})
    move, z = cam.get("move", "none"), cam.get("zoom", 1.12)
    p = ease(t / length) if length > 0 else 0
    cx = cy = 0.5
    zoom = 1.0
    if move == "push_in":
        zoom = 1 + (z - 1) * p
    elif move == "pull_out":
        zoom = z - (z - 1) * p
    elif move in ("pan_left", "pan_right"):
        zoom = z
        span = (1 - 1 / z) / 2 * 0.9
        cx = 0.5 + (span * (1 - 2 * p) if move == "pan_left" else span * (2 * p - 1))
    f = cam.get("focus")
    if f and zoom > 1:
        cx += (f[0] - 0.5) * (1 - 1 / zoom)
        cy += (f[1] - 0.5) * (1 - 1 / zoom)
    sh = shot.get("shake")
    shx = shy = 0.0
    if sh and sh["at"] <= t < sh["at"] + sh.get("dur", 0.4):
        k = (1 - (t - sh["at"]) / sh.get("dur", 0.4)) * sh.get("amp", 8)
        shx, shy = k * math.sin(t * 90), k * math.cos(t * 77)
    return zoom, cx, cy, shx, shy


def _gestures(ln):
    """[{at, dur, type}] seconds from the line start. 'gesture' alone = the whole line."""
    if ln.get("gestures"):
        return ln["gestures"]
    g = ln.get("gesture", "none")
    return [] if g == "none" else [{"at": 0.0, "dur": ln["dur"], "type": g}]


def _segments(job, cid, fps):
    """Per-character line segments with mouth states."""
    segs = []
    for ln in job["lines"]:
        if ln["speaker"] != cid:
            continue
        n = max(1, round(ln["dur"] * fps))
        states = audio.mouth_states(ln["audio_path"], fps) if ln["audio_path"] \
            else audio.fake_states(n, ln["id"])
        energy = np.convolve(states / 2.0, np.ones(3) / 3, mode="same")
        segs.append({"s": ln["local_start"], "e": ln["local_start"] + ln["dur"],
                     "states": states, "energy": energy, "emotion": ln.get("emotion", "neutral"),
                     "gestures": _gestures(ln), "move_to": ln.get("move_to")})
    return segs


def _blinks(cid, si, length):
    rng = np.random.default_rng(zlib.crc32(f"{cid}{si}".encode()))
    t, out = float(rng.uniform(0.8, 2.5)), []
    while t < length:
        out.append(t)
        t += float(rng.uniform(2.5, 4.5))
    return out


def render_shot(args):
    series_dir, cfg, job, out_path = args
    W, H, fps = cfg["width"], cfg["height"], cfg["fps"]
    spec, n = job["spec"], job["nframes"]
    length = n / fps
    cam = spec.get("camera", {})
    S = max(1.0, cam.get("zoom", 1.12) if cam.get("move", "none") != "none" else 1.0,
            1.05 if spec.get("shake") else 1.0)
    WW, WH = round(W * S), round(H * S)

    bg = Image.open(find_background(series_dir, spec["background"])).convert("RGB")
    sc = max(WW / bg.width, WH / bg.height)
    bg = bg.resize((math.ceil(bg.width * sc), math.ceil(bg.height * sc)), Image.LANCZOS)
    l, t0 = (bg.width - WW) // 2, (bg.height - WH) // 2
    bg = bg.crop((l, t0, l + WW, t0 + WH))

    actors = []
    for c in spec.get("characters", []):
        ch = _char(series_dir, c["id"])
        k = ch.height_ratio * H * S * c.get("scale", 1.0) / ch.ch
        pos = c.get("pos", [0.5, 0.95])
        segs = _segments(job, c["id"], fps)
        moves, cur = [], list(pos)
        for sg in segs:
            if sg["move_to"]:
                moves.append((sg["s"], sg["s"] + 0.8, list(cur), list(sg["move_to"])))
                cur = list(sg["move_to"])
        actors.append({"ch": ch, "k": k, "pos": pos, "flip": c.get("flip", False),
                       "enter": c.get("enter", "none"), "exit": c.get("exit", "none"),
                       "enter_at": c.get("enter_at", 0.0), "exit_at": c.get("exit_at", length - 0.7),
                       "segs": segs, "moves": moves, "blinks": _blinks(c["id"], job["index"], length),
                       "phase": (zlib.crc32(c["id"].encode()) % 628) / 100})
    actors.sort(key=lambda a: a["pos"][1])

    font = subtitles.load_font(series_dir, cfg) if cfg["subtitles"].get("burn_in") else None
    fade = spec.get("transition") == "fade"
    black = Image.new("RGB", (W, H), (0, 0, 0))

    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", "-an", out_path], stdin=subprocess.PIPE)

    for f in range(n):
        t = f / fps
        world = bg.copy()
        for a in actors:
            ch = a["ch"]
            seg = next((s for s in a["segs"] if s["s"] <= t < s["e"]), None)
            past = [s for s in a["segs"] if s["s"] <= t]
            emotion = past[-1]["emotion"] if past else "neutral"
            mouth, energy, gest, gf = 0, 0.0, "none", 0.0
            if seg:
                idx = min(int((t - seg["s"]) * fps), len(seg["states"]) - 1)
                mouth, energy = int(seg["states"][idx]), float(seg["energy"][idx])
                for g in seg["gestures"]:
                    lt = t - seg["s"] - g["at"]
                    if 0 <= lt < g["dur"]:
                        gest, gf = g["type"], gesture_factor(lt, g["dur"])
            blink = any(0 <= t - b < 0.14 for b in a["blinks"])
            amp = 3.0 + (4.0 if seg else 0.0)
            eye = (amp * math.sin(2 * math.pi * t / 1.7 + a["phase"]),
                   amp * 0.5 * math.sin(2 * math.pi * t / 2.3 + a["phase"] * 2))
            angles = ch.arm_angles(gest, gf, t)
            spr, fx, fy = ch.sprite(a["k"], mouth, blink, eye, angles, emotion, a["flip"], gest)

            px, py = a["pos"]
            for (m0, m1, p0, p1) in a["moves"]:
                if t >= m0:
                    e = ease((t - m0) / (m1 - m0))
                    px, py = p0[0] + (p1[0] - p0[0]) * e, p0[1] + (p1[1] - p0[1]) * e
            if a["enter"] in ("left", "right"):
                e = ease((t - a["enter_at"]) / 0.6)
                off = -0.35 if a["enter"] == "left" else 1.35
                px = off + (px - off) * e
            if a["exit"] in ("left", "right") and t > a["exit_at"]:
                e = ease((t - a["exit_at"]) / 0.6)
                off = -0.35 if a["exit"] == "left" else 1.35
                px = px + (off - px) * e
            bob = math.sin(2 * math.pi * t / 2.4 + a["phase"]) * 0.004 * WH + energy * 0.012 * WH
            world.paste(spr, (round(px * WW - fx), round(py * WH - fy - bob)), spr)

        zoom, cx, cy, shx, shy = _camera(spec, t, length)
        bw, bh = WW / zoom, WH / zoom
        x0 = min(max(cx * WW - bw / 2 + shx, 0), WW - bw)
        y0 = min(max(cy * WH - bh / 2 + shy, 0), WH - bh)
        frame = world.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + bw, y0 + bh))

        if font:
            for ln in job["lines"]:
                if ln["local_start"] <= t < ln["local_start"] + ln["dur"]:
                    subtitles.draw(frame, ln["text"], font, cfg)
                    break
        if fade:
            a_ = min(1.0, t / 0.25, (length - t) / 0.25)
            if a_ < 1.0:
                frame = Image.blend(black, frame, max(0.0, a_))
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait()
    return job["index"], out_path


def render_all(series_dir, cfg, timeline, work_dir, workers=None):
    os.makedirs(work_dir, exist_ok=True)
    jobs = [(series_dir, cfg, sh, os.path.join(work_dir, f"shot_{sh['index']:03d}.mp4"))
            for sh in timeline["shots"]]
    with Pool(workers or min(4, os.cpu_count() or 1)) as pool:
        done = sorted(pool.imap_unordered(render_shot, jobs))
    lst = os.path.join(work_dir, "concat.txt")
    with open(lst, "w") as f:
        for _, p in done:
            f.write(f"file '{os.path.abspath(p)}'\n")
    silent = os.path.join(work_dir, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", silent], check=True)
    return silent
