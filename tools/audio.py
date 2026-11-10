"""Audio helpers: durations, loudness envelope -> mouth states, final mix."""
import os
import subprocess
import tempfile

import numpy as np

SR = 16000
AUDIO_EXT = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac")


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def find_line_audio(episode_dir, line):
    """audio/001.wav (any extension) for line id 1, or an explicit line['audio'] path."""
    if line.get("audio"):
        p = os.path.join(episode_dir, line["audio"])
        return p if os.path.exists(p) else None
    for ext in AUDIO_EXT:
        p = os.path.join(episode_dir, "audio", f"{int(line['id']):03d}{ext}")
        if os.path.exists(p):
            return p
    return None


def estimated_duration(text):
    return max(1.2, len(text.split()) * 0.42 + 0.4)


def _load_mono(path):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def mouth_states(path, fps):
    """Per-frame mouth state from loudness: 0 closed, 1 half, 2 open (no phonemes)."""
    x = _load_mono(path)
    hop = SR / fps
    n = max(1, int(np.ceil(len(x) / hop)))
    env = np.zeros(n)
    for i in range(n):
        seg = x[int(i * hop): int((i + 1.5) * hop)]
        env[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0.0
    ref = np.percentile(env, 95)
    if ref < 1e-4:
        return np.zeros(n, dtype=int)
    v = env / ref
    s = np.where(v < 0.2, 0, np.where(v < 0.55, 1, 2)).astype(int)
    out = s.copy()
    for i in range(1, n - 1):  # drop single-frame flicker
        out[i] = int(np.median(s[i - 1: i + 2]))
    return out


def fake_states(n, seed):
    """Stand-in mouth movement when the line has no audio file yet."""
    rng = np.random.default_rng(seed)
    out, i = np.zeros(n, dtype=int), 0
    while i < n:
        run = int(rng.integers(2, 5))
        out[i:i + run] = int(rng.choice([0, 1, 2, 2]))
        i += run
    return out


def mix(entries, total, out_path, music=None):
    """entries: [(path, start_seconds, volume)], music: (path, volume) or None."""
    cmd = ["ffmpeg", "-v", "error", "-y"]
    chains, labels = [], []
    for i, (p, start, vol) in enumerate(entries):
        cmd += ["-i", p]
        ms = int(round(start * 1000))
        chains.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                      f"volume={vol},adelay={ms}|{ms}[a{i}]")
        labels.append(f"[a{i}]")
    n = len(entries)
    if music:
        mp, mvol = music
        cmd += ["-stream_loop", "-1", "-i", mp]
        chains.append(f"[{n}:a]aresample=44100,aformat=channel_layouts=stereo,"
                      f"atrim=0:{total:.3f},volume={mvol},afade=t=out:st={max(0, total - 2):.3f}:d=2[m]")
        labels.append("[m]")
    if not labels:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{total:.3f}", out_path]
        subprocess.run(cmd, check=True)
        return
    chains.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,"
                  f"apad=whole_dur={total:.3f},atrim=0:{total:.3f},"
                  "loudnorm=I=-16:TP=-1.5:LRA=11[out]")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(";\n".join(chains))
        script = f.name
    cmd += ["-filter_complex_script", script, "-map", "[out]", "-ar", "44100", out_path]
    try:
        subprocess.run(cmd, check=True)
    finally:
        os.unlink(script)
