# Arabic kids' cartoon episodes: production workflow

The owner sends a **script** for a new episode. Claude turns it into a finished video for review. The characters,
backgrounds, voices and style are set up once in `series/` and reused for every episode.

Style: 2D cut-out cartoon. Flat characters with thick outlines move over background images: mouth opens/closes with the
voice (by loudness, no lip-sync), eyes wiggle and blink, arms raise/point/wave, simple camera moves and fades.

## When the owner sends a script

1. **Read the script** (any format, see `docs/WORKFLOW.md`). Check it is age-appropriate (no scary/dangerous
   imitable behaviour). If something is questionable, say so before rendering.
2. **List what exists**: `ls series/characters series/backgrounds` and read `series/voices/voices.json`.
   Only use characters and backgrounds that exist. If the script needs a missing one, stop and tell the owner exactly
   what to add (name + what it should look like). Never invent placeholder art for a real episode.
3. **Write `episodes/<ep-id>/scene.json`** (format below). Keep the dialogue exactly as written by the owner.
4. **Export the voice lines**: `.venv/bin/python tools/kids.py lines --episode episodes/<ep-id>` writes `lines.txt`
   (numbered lines + speaker + voice note). Give it to the owner to record, or generate audio if an automatic voice
   provider has been set up in `series/voices/voices.json`. Audio goes to `episodes/<ep-id>/audio/001.mp3` (line id,
   3 digits; .wav/.m4a/.ogg also work).
5. **Validate**: `.venv/bin/python tools/kids.py validate --episode episodes/<ep-id>`.
6. **Render**: `.venv/bin/python tools/kids.py render --episode episodes/<ep-id>`.
   Output in `episodes/<ep-id>/out/`: `final.mp4`, `final.srt`, `qc.json`, `contact_sheet.jpg`.
   Without audio files the timing is estimated and the mouths move randomly. That is a preview only.
7. **Look at `contact_sheet.jpg` and `qc.json`** before reporting. Report warnings honestly. Fix what is fixable
   (e.g. wrong character position, subtitle over a face) and re-render.
8. **Never publish.** The owner reviews and uploads manually.

Setup once per session: `python3 -m venv .venv --system-site-packages && .venv/bin/pip install -r requirements.txt`
(ffmpeg must be installed). Always run the tools with `.venv/bin/python`.

## scene.json

```json
{"title": "...", "shots": [{
  "background": "street",                       // file name in series/backgrounds/ (no extension)
  "camera": {"move": "push_in", "zoom": 1.12},  // none | push_in | pull_out | pan_left | pan_right; optional focus [x,y]
  "transition": "fade",                         // cut (default) | fade (dip to black at both ends)
  "shake": {"at": 2.8, "dur": 0.4, "amp": 8},   // optional camera shake, seconds from shot start
  "characters": [{"id": "ahmed", "pos": [0.3, 0.97], "scale": 1.0, "flip": false, "enter": "left", "exit": "none"}],
  "lines": [{"id": 1, "speaker": "ahmed", "text": "...", "emotion": "neutral",
             "gesture": "raise", "move_to": [0.5, 0.97]}],
  "sfx": [{"file": "sfx/pop.wav", "at": 0.5, "volume": 0.8}],
  "pad_before": 0.3, "pad_after": 0.5, "duration": 2.0     // duration only for shots without lines
}]}
```

- `pos` = [x centre, feet line] as fractions of the frame (0..1). Feet around 0.95 to 0.97. `flip: true` mirrors the character so it faces left.
- `enter`/`exit`: `left` or `right` slide in/out (0.6 s). `move_to` walks the speaker during the first 0.8 s of a line.
- `gesture`: `none`, `raise`, `point`, `wave`, `both_raise`. Applies to the speaker's main arm while they talk.
- `emotion`: swaps the images listed under `emotions` in `character.json` (if defined). Otherwise ignored.
- Line `id`s are unique, increasing from 1 across the whole episode. Shots of about 4 to 12 seconds, 1 to 3 lines each.
- Vary camera moves between shots. Use `fade` for scene changes, `cut` inside a scene.
- Keep subtitles clear of faces: characters at the sides, or lower `subtitles.bottom` in `series.json`.

## Project layout

- `series/`: the one-time setup: `series.json` (resolution, fps, font, music), `characters/<id>/` (layered PNGs +
  `character.json`), `backgrounds/`, `voices/voices.json`, `music/`, `sfx/`, `fonts/`. Spec: `series/README.md`.
- `episodes/<ep-id>/`: `script.md` (owner), `scene.json` (Claude), `audio/`, `out/`.
- `tools/`: renderer and CLI. `tools/make_demo.py` builds a placeholder demo in `demo/` to test the pipeline.
- `docs/`: research report and cost decision (earlier phase).

## Known limits

- Mouth movement follows loudness only, so it looks right for cartoons but is not phoneme lip-sync.
- Arm rotation uses the pivot in `character.json`; leave transparent padding in the layer so a raised arm is not clipped.
- Voices: not automated yet. Child-like Arabic voices have not been verified with any provider (test first).
- Burned-in Arabic subtitles use DejaVu Sans unless `series/fonts/` holds another font set in `series.json`.
