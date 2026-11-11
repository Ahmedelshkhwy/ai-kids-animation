# Series setup (done once)

Everything here is reused by every episode. Replace the examples with your real art.

## 1. Characters: `characters/<id>/`

Export each character as **separate transparent PNGs, all the same canvas size** (a layered file exported layer by
layer from Procreate / Photoshop / Figma / Krita does exactly this). Leave empty space around the character so a raised
arm is not cut off.

| Layer | Needed | Notes |
|---|---|---|
| Body + head | yes | without eyes, mouth and arms; legs and feet included |
| Eyes open | yes | dots or full eyes, as a separate layer |
| Eyes closed | optional | used for blinking |
| Mouth closed / open | yes | add **half-open** for smoother talking |
| Arm(s) | optional | hanging down along the body, one PNG per arm |
| Extra expressions | optional | alternative mouth/eyes/arms for `sad`, `angry`, ... |

`character.json` (example in `demo/series/characters/ahmed/`):

```json
{
  "name": "ahmed",
  "canvas": [500, 800],
  "height_ratio": 0.62,
  "feet": [250, 788],
  "layers": [
    {"role": "arm", "id": "left", "image": "arm_left.png", "pivot": [170, 330], "up": -150, "point": -95},
    {"role": "static", "image": "body.png"},
    {"role": "eyes", "open": "eyes_open.png", "closed": "eyes_closed.png"},
    {"role": "mouth", "closed": "mouth_closed.png", "half": "mouth_half.png", "open": "mouth_open.png"},
    {"role": "arm", "id": "right", "image": "arm_right.png", "pivot": [330, 330], "up": 150, "point": 95, "main": true}
  ],
  "emotions": {"sad": {"mouth": {"closed": "mouth_sad.png"}}}
}
```

- Layers are drawn first to last (back to front). Put an arm *before* the body to draw it behind.
- `pivot` = the shoulder point in canvas pixels. `up` / `point` = rotation in degrees (counter-clockwise is positive)
  for a raised / pointing arm. An arm on the right side of the image uses a positive angle, on the left a negative one.
- An arm layer can have `"poses": {"rest": "...", "open": "...", "point": "..."}`: arm images with different hands (fist / open hand / pointing); the gesture picks the pose. See `characters/sunbul/`.
- `main: true` marks the arm used for `raise` / `point` / `wave`. `both_raise` moves all arms.
- `height_ratio` = character height as a fraction of the frame height. `feet` = where the feet touch the ground.
- Eyes that are just two dots work: the whole eye layer drifts a few pixels so they look alive.

## 2. Backgrounds: `backgrounds/<name>.png`

One image per place (home, street, garden...), same art style as the characters. Use landscape **16:9, 1920x1080 or
larger**; the camera zooms in, so more pixels = sharper. Use the same aspect ratio as `series.json`.

## 3. `series.json`

```json
{"name": "my-series", "width": 1280, "height": 720, "fps": 24,
 "font": "fonts/Cairo-Bold.ttf", "gap": 0.25,
 "subtitles": {"burn_in": true, "size": 46, "bottom": 0.08},
 "music": {"file": "music/theme.mp3", "volume": 0.12}}
```

Use `1080x1920` for vertical (Shorts/Reels) or `1920x1080` for YouTube. Width and height must be even.
`font` and `music` are optional (the font must support Arabic).

## 4. Voices: `voices/voices.json`

```json
{"ahmed": {"provider": "manual", "note": "boy, 8 years, street kid, Egyptian dialect, lively"}}
```

For now, record each line yourself (ElevenLabs or any tool) and save it as `episodes/<ep>/audio/001.mp3`, `002.mp3`... in the
order of `lines.txt`. The `note` is printed next to each line so the voice stays consistent.

## 5. Music and SFX

Put royalty-free tracks in `music/` and short sounds in `sfx/`. Keep a note of each file's source and licence.
