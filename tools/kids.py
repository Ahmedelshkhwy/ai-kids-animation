#!/usr/bin/env python3
"""Episode production CLI.

  python3 tools/kids.py validate --series series --episode episodes/ep-001
  python3 tools/kids.py lines    --series series --episode episodes/ep-001   # numbered lines for voice recording
  python3 tools/kids.py render   --series series --episode episodes/ep-001   # video + srt + qc + contact sheet
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audio  # noqa: E402
import qc  # noqa: E402
import render  # noqa: E402
import scene as sc  # noqa: E402
import subtitles  # noqa: E402


def load(args):
    cfg = sc.load_series(args.series)
    scene = sc.load_json(os.path.join(args.episode, "scene.json"))
    return cfg, scene


def cmd_validate(args):
    cfg, scene = load(args)
    errors, warnings = sc.validate(scene, cfg, args.series, args.episode)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


def cmd_lines(args):
    cfg, scene = load(args)
    voices_path = os.path.join(args.series, "voices", "voices.json")
    voices = sc.load_json(voices_path) if os.path.exists(voices_path) else {}
    out = os.path.join(args.episode, "lines.txt")
    with open(out, "w", encoding="utf-8") as f:
        for shot in scene["shots"]:
            for ln in shot.get("lines", []):
                v = voices.get(ln["speaker"], {}).get("note", "")
                f.write(f"{int(ln['id']):03d} | {ln['speaker']} | {ln['text']}"
                        + (f"   ({v})" if v else "") + "\n")
    print("wrote", out, "- save each recorded line as audio/<number>.mp3 (or .wav/.m4a)")


def cmd_render(args):
    cfg, scene = load(args)
    errors, warnings = sc.validate(scene, cfg, args.series, args.episode)
    if errors:
        print("\n".join("ERROR " + e for e in errors))
        return 1
    tl = sc.build_timeline(scene, cfg, args.episode)
    out_dir = os.path.join(args.episode, "out")
    work = os.path.join(out_dir, "work")
    os.makedirs(out_dir, exist_ok=True)
    print(f"{len(tl['shots'])} shots, {tl['total']:.1f}s, {cfg['width']}x{cfg['height']}@{cfg['fps']}")
    silent = render.render_all(args.series, cfg, tl, work, args.workers)

    entries = [(ln["audio_path"], sh["start"] + ln["local_start"], 1.0)
               for sh in tl["shots"] for ln in sh["lines"] if ln["audio_path"]]
    for sh in tl["shots"]:
        for fx in sh["spec"].get("sfx", []):
            p = os.path.join(args.series, fx["file"])
            if os.path.exists(p):
                entries.append((p, sh["start"] + fx["at"], fx.get("volume", 0.8)))
    music = None
    m = cfg.get("music")
    if m and os.path.exists(os.path.join(args.series, m["file"])):
        music = (os.path.join(args.series, m["file"]), m.get("volume", 0.12))
    mixed = os.path.join(work, "mix.wav")
    audio.mix(entries, tl["total"], mixed, music)

    final = os.path.join(out_dir, "final.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", mixed, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final], check=True)
    subtitles.write_srt(tl, os.path.join(out_dir, "final.srt"))
    missing = [ln["id"] for sh in tl["shots"] for ln in sh["lines"] if not ln["audio_path"]]
    report = qc.run_qc(final, tl, cfg, missing, os.path.join(out_dir, "qc.json"),
                       os.path.join(out_dir, "contact_sheet.jpg"))
    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    print("video:", final)
    print("QC:", "OK" if report["ok"] else "warnings")
    for w in report["warnings"]:
        print("  -", w)
    print("info:", report["info"])
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate", "lines", "render"])
    ap.add_argument("--series", default="series")
    ap.add_argument("--episode", required=True)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--keep-work", action="store_true")
    args = ap.parse_args()
    sys.exit({"validate": cmd_validate, "lines": cmd_lines, "render": cmd_render}[args.cmd](args))


if __name__ == "__main__":
    main()
