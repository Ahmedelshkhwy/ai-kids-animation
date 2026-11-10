# AI Kids Animation

Reusable pipeline for Arabic kids' cartoon episodes: set up the characters, backgrounds and voices once in `series/`,
then send only a script for each episode and get a finished video to review.

- `CLAUDE.md`: how an episode is produced (what Claude does when a script arrives)
- `series/README.md`: what to prepare once (characters, backgrounds, voices)
- `docs/WORKFLOW.md`: the script format and the steps per episode
- `docs/decision.md`, `docs/research-report.md`: earlier research and cost decision
- `tools/`: renderer. Test it with `python3 tools/make_demo.py` (placeholder art in `demo/`)

Setup: `python3 -m venv .venv --system-site-packages && .venv/bin/pip install -r requirements.txt` (needs ffmpeg).
