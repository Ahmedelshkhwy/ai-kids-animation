"""Automated checks on the rendered episode + a contact sheet for quick review."""
import json
import re
import subprocess

from PIL import Image


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries",
              "format=duration:stream=codec_type,width,height,r_frame_rate", "-of", "json", path])
    return json.loads(r.stdout)


def loudness(path):
    r = _run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af",
              "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    return json.loads(m.group(0)) if m else {}


def contact_sheet(video, timeline, out_path, cfg, cols=4, tw=480):
    th = round(tw * cfg["height"] / cfg["width"])
    thumbs = []
    for sh in timeline["shots"]:
        mid = sh["start"] + sh["nframes"] / cfg["fps"] / 2
        tmp = out_path + f".{sh['index']}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mid:.2f}", "-i", video, "-frames:v", "1",
                        "-vf", f"scale={tw}:{th}", tmp], check=True)
        thumbs.append(tmp)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (30, 30, 30))
    import os
    for i, p in enumerate(thumbs):
        sheet.paste(Image.open(p), ((i % cols) * tw, (i // cols) * th))
        os.unlink(p)
    sheet.save(out_path, quality=88)


def run_qc(video, timeline, cfg, missing_audio, out_json, sheet_path):
    warnings, info = [], {}
    pr = probe(video)
    streams = {s["codec_type"]: s for s in pr["streams"]}
    dur = float(pr["format"]["duration"])
    info["duration"] = round(dur, 2)
    info["expected_duration"] = round(timeline["total"], 2)
    if "video" not in streams:
        warnings.append("no video stream")
    elif (streams["video"]["width"], streams["video"]["height"]) != (cfg["width"], cfg["height"]):
        warnings.append("unexpected resolution")
    if "audio" not in streams:
        warnings.append("no audio stream")
    if abs(dur - timeline["total"]) > 0.3:
        warnings.append(f"duration {dur:.2f}s differs from expected {timeline['total']:.2f}s")
    for lid in missing_audio:
        warnings.append(f"line {lid}: audio file missing, timing was estimated")

    ln = loudness(video)
    if ln:
        info["loudness_lufs"] = float(ln["input_i"])
        info["true_peak_db"] = float(ln["input_tp"])
        if float(ln["input_i"]) < -24 or float(ln["input_i"]) > -9:
            warnings.append(f"loudness {ln['input_i']} LUFS is outside the usual -24..-9 range")

    r = _run(["ffmpeg", "-hide_banner", "-i", video, "-vf", "blackdetect=d=0.6:pix_th=0.08",
              "-an", "-f", "null", "-"])
    for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr):
        warnings.append(f"black frames {m.group(1)}s-{m.group(2)}s")
    r = _run(["ffmpeg", "-hide_banner", "-i", video, "-af", "silencedetect=noise=-45dB:d=3.5",
              "-vn", "-f", "null", "-"])
    for m in re.finditer(r"silence_start: ([\d.]+)", r.stderr):
        warnings.append(f"long silence starting at {m.group(1)}s")

    contact_sheet(video, timeline, sheet_path, cfg)
    report = {"ok": not warnings, "warnings": warnings, "info": info}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report
