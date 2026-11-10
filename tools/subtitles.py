"""SRT export and Arabic subtitle burn-in (reshaping + bidi)."""
import os

from PIL import ImageDraw, ImageFont, features

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:  # burn-in then falls back to raw text
    arabic_reshaper = None

DEFAULT_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
# With libraqm Pillow shapes and reorders Arabic itself; without it we do it manually.
RAQM = features.check("raqm")
_KW = {"direction": "rtl", "language": "ar"} if RAQM else {}


def _ts(sec):
    ms = int(round(sec * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def write_srt(timeline, path):
    n = 0
    with open(path, "w", encoding="utf-8") as f:
        for sh in timeline["shots"]:
            for ln in sh["lines"]:
                n += 1
                s = sh["start"] + ln["local_start"]
                f.write(f"{n}\n{_ts(s)} --> {_ts(s + ln['dur'])}\n{ln['text']}\n\n")


def _shape(text):
    if RAQM or arabic_reshaper is None:
        return text
    return get_display(arabic_reshaper.reshape(text))


def load_font(series_dir, cfg):
    name = cfg.get("font")
    path = os.path.join(series_dir, name) if name else DEFAULT_FONT
    if not os.path.exists(path):
        path = DEFAULT_FONT
    return ImageFont.truetype(path, cfg["subtitles"]["size"])


def draw(frame, text, font, cfg):
    W, H = frame.size
    d = ImageDraw.Draw(frame)
    max_w = W * 0.86
    lines, cur = [], ""
    for w in text.split():
        cand = (cur + " " + w).strip()
        if cur and font.getlength(_shape(cand), **_KW) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = cand
    lines.append(cur)
    lh = font.size * 1.35
    y = H - H * cfg["subtitles"]["bottom"] - lh * len(lines)
    for ln in lines:
        s = _shape(ln)
        x = (W - font.getlength(s, **_KW)) / 2
        d.text((x, y), s, font=font, fill="white", stroke_width=max(2, font.size // 14),
               stroke_fill="black", **_KW)
        y += lh
