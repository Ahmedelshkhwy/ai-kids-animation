"""Scene script (scene.json) loading, validation and timeline."""
import json
import os

import audio

GESTURES = {"none", "raise", "point", "wave", "both_raise"}
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_series(series_dir):
    cfg = {"width": 1280, "height": 720, "fps": 24, "gap": 0.25,
           "subtitles": {"burn_in": True, "size": 46, "bottom": 0.08}}
    cfg.update(load_json(os.path.join(series_dir, "series.json")))
    return cfg


def find_background(series_dir, name):
    for ext in IMG_EXT:
        p = os.path.join(series_dir, "backgrounds", name + ext)
        if os.path.exists(p):
            return p
    return None


def build_timeline(scene, cfg, ep_dir):
    """Absolute and shot-local timing for every shot and line."""
    fps, gap = cfg["fps"], cfg.get("gap", 0.25)
    t, shots = 0.0, []
    for si, shot in enumerate(scene["shots"]):
        local = shot.get("pad_before", 0.3)
        lines = []
        for line in shot.get("lines", []):
            ap = audio.find_line_audio(ep_dir, line)
            dur = audio.duration(ap) if ap else audio.estimated_duration(line["text"])
            lines.append({**line, "audio_path": ap, "local_start": local, "dur": dur})
            local += dur + gap
        if lines:
            length = local - gap + shot.get("pad_after", 0.5)
        else:
            length = shot.get("duration", 2.0)
        nframes = max(1, round(length * fps))
        shots.append({"index": si, "start": t, "nframes": nframes, "spec": shot, "lines": lines})
        t += nframes / fps
    return {"shots": shots, "total": t}


def validate(scene, cfg, series_dir, ep_dir):
    errors, warnings = [], []
    if cfg["width"] % 2 or cfg["height"] % 2:
        errors.append("series.json width/height must be even numbers")
    seen_ids, chars_checked = set(), {}
    for si, shot in enumerate(scene.get("shots", []), 1):
        tag = f"shot {si}"
        bg = shot.get("background")
        if not bg or not find_background(series_dir, bg):
            errors.append(f"{tag}: background '{bg}' not found in series/backgrounds/")
        present = set()
        for c in shot.get("characters", []):
            cid = c["id"]
            present.add(cid)
            if cid not in chars_checked:
                chars_checked[cid] = _check_character(series_dir, cid, errors)
        for line in shot.get("lines", []):
            lid = line.get("id")
            if lid in seen_ids or lid is None:
                errors.append(f"{tag}: line id {lid} missing or duplicated")
            seen_ids.add(lid)
            if line.get("speaker") not in present:
                errors.append(f"{tag} line {lid}: speaker '{line.get('speaker')}' is not in the shot's characters")
            g = line.get("gesture", "none")
            if g not in GESTURES:
                errors.append(f"{tag} line {lid}: unknown gesture '{g}' (use {sorted(GESTURES)})")
            if not audio.find_line_audio(ep_dir, line):
                warnings.append(f"line {lid}: no audio file (audio/{int(lid):03d}.*), timing is estimated")
    return errors, warnings


def _check_character(series_dir, cid, errors):
    d = os.path.join(series_dir, "characters", cid)
    cj = os.path.join(d, "character.json")
    if not os.path.exists(cj):
        errors.append(f"character '{cid}': missing {cj}")
        return False
    cfg = load_json(cj)
    files = []
    for L in cfg["layers"]:
        for k in ("image", "open", "closed", "half"):
            if L.get(k):
                files.append(L[k])
    for emo in cfg.get("emotions", {}).values():
        for role in emo.values():
            files += list(role.values())
    for fn in files:
        if not os.path.exists(os.path.join(d, fn)):
            errors.append(f"character '{cid}': missing image {fn}")
    return True
