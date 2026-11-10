# Workflow for a new episode

## What you send

A script in any readable form. This format works well:

```
# Episode title
Place: street
Characters: Ahmed (left), Mona (right)

Ahmed (excited, raises hand): Hi Mona! Come and play!
Mona: I can't, I have homework first.
[Mona walks to the right and leaves]
Place: garden
...
```

Write the dialogue in the language and dialect you want in the video. Mention places and characters by the names used
in `series/`. Gestures, emotions and movements in brackets are optional, otherwise Claude chooses them.

## What happens

1. Claude checks the script and that all characters and places exist.
2. Claude writes `scene.json` (shots, camera, gestures) and a numbered `lines.txt` for the voices.
3. You record the lines (ElevenLabs etc.) and drop the files into `episodes/<ep>/audio/` as `001.mp3`, `002.mp3`...
4. Claude renders `out/final.mp4` + `final.srt` + a contact sheet + QC report, and tells you honestly what it found.
5. You watch, ask for changes (timing, gestures, camera, wording), and publish yourself.

Rendering speed (demo, 4 CPU cores): about 0.5 s of work per second of video. A 3-minute episode should take
roughly 1.5 to 2 minutes (not yet measured with real art).

## Changing things later

- New character or place: add the files to `series/`, nothing else changes.
- New look for the whole series: change `series.json` (size, subtitles, music).
- A different renderer or voice tool can be swapped in without touching the scripts, because `scene.json` and the audio
  files are the only contract between the steps.
