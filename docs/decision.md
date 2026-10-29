# Decision: Build our own system, or use an AI video platform?

**Scope:** Arabic children's cartoon episodes, 5 minutes each, produced continuously. The only manual step should be review and publishing.
**Prices checked:** 29 Oct 2026. ✅ = official vendor page. ⚠️ = third-party source or conflicting sources. *(est.)* = my arithmetic from the stated assumptions.

---

## 1. Short answer

**Yes, it can be built, and building it is worth it,** under two conditions:

1. The visual style must be **2D cut-out (puppet) animation**: reusable character rigs, lip-synced mouths, camera moves and transitions, all rendered by code. A cinematic or 3D look can't be produced repeatedly without paying a video platform for every episode.
2. You must accept **4–8 weeks of setup** before the first automated episode. After that, each episode costs about **$0.50–$1.50** and **15–30 minutes** of your review time.

Arabic is the main quality risk. It affects voice expressiveness and lip-sync precision, and should be tested first, before anything else is built.

---

## 2. Which components are free, and which are paid or manual

| Component | Free, local, open source | Paid, cloud or manual alternative | Choice for Option A |
|---|---|---|---|
| Story ideas, Arabic script, scene breakdown | Gemini 3.8 Flash free tier ✅. Your data may be used by Google, and the free limits are low and change often. Local LLMs are weak at Arabic creative writing. | Claude Sonnet 5.5 at $2 / $10 per 1M input/output tokens ✅ | **Paid**: Claude, about $0.30–0.60 per episode including retries *(est.)* |
| Arabic voices | SILMA TTS: Apache-2.0, MSA (Fusha), voice cloning from <8 s of audio, 150M params ✅. Chatterbox Multilingual: MIT, includes Arabic ✅. Expressiveness and child-voice quality are **unproven**. | ElevenLabs: API $0.08 per 1k characters (v3/v4) ✅. Creator plan $22/mo for 121k credits ✅. Commercial license only from Starter ($6) upward ✅. | **Test both.** Budget for ElevenLabs; switch to SILMA if it sounds good enough. |
| Lip-sync | Rhubarb (MIT ✅). Arabic must use its language-independent "phonetic" mode, which is less precise ✅. | — | **Free** |
| Character design (one-time) | FastSD CPU on your laptop (slow) | Nano Banana 2.1 at $0.0336 per 1K image ✅ | About $5–15, one time |
| Splitting characters into rig layers (one-time) | Qwen-Image-Layered, Apache-2.0 ✅. It needs a cloud GPU (20B model). | Rented GPU, e.g. RunPod 4090 at about $0.34/h ⚠️ | About $5–20 one time, **plus manual cleanup** |
| Backgrounds and props | Cloudflare Workers AI: 10k free "neurons"/day ✅, roughly 100–170 FLUX images/day *(est.)* | $0.011 per 1k neurons beyond the free tier ✅ | **Free**, reused from a library |
| Music and sound effects | Curated royalty-free library | — | **Free** (one-time curation) |
| Animation, render, mix, subtitles | Remotion (free for individuals and companies with ≤3 employees ✅), FFmpeg, Arabic SRT subtitles | Remotion company license if you grow past 3 employees | **Free**, runs on your laptop CPU |
| Quality checks | FFmpeg filters, faster-whisper (Arabic transcript vs script) | A vision-LLM spot check costs a few cents | About $0.05 |
| **Manual work** | — | Character design approval, rig cleanup (one-time); about 20 minutes of review per episode (ongoing) | — |

**Paid dependencies in Option A, stated plainly:** an LLM API (about $3–20/month), ElevenLabs (about $22/month, unless SILMA is good enough), and a small one-time cloud GPU and image-generation cost. Everything else is free and runs on your laptop.

---

## 3. The two options

**A. Build and operate our own system** (2D puppets, Arabic voice, automated pipeline)
Script → scene JSON → Arabic TTS → visemes → render → mix → QC → review package.

**B. Use an AI video platform directly**
Gemini Omni Flash (Google's replacement for Veo 3.1) or Kling generates the shots. ElevenLabs provides the Arabic voice. Lip-sync and editing are done in the platform or CapCut. The same AI script writer is used.

Facts that matter for Option B:
- **Gemini Omni Flash:** about **$0.10 per second at 720p**, and **no free tier** ✅ ([Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing)).
- **Veo 3.1 previews were shut down on 22 Oct 2026** ✅ ([Veo docs](https://ai.google.dev/gemini-api/docs/veo)). Models get replaced often.
- **Arabic speech in Veo:** Google says only **English is fully supported**; other languages "have not been evaluated" ✅. Arabic dialogue would therefore come from separate TTS plus a separate lip-sync step.
- **Character consistency in Veo 3.1:** at most **3 reference images** per clip, and clips are **≤8 s** ✅. A 5-minute episode needs 40 or more separately generated clips.
- **Kling:** about **$0.08 per second** ⚠️ (Standard mode, roughly $0.40 per 5 s clip). Plans run from $10 to $180/month ⚠️; per-clip credit costs are disputed between sources.

---

## 4. Comparison, including failed outputs

**Assumptions:**
- A 5-minute episode has about 4,000 Arabic characters of dialogue.
- **Option A:** script generation is retried about 2×, about 30% of voice lines are regenerated, and re-renders are free (laptop time only).
- **Option B:** each usable clip takes about **3 generations** on average (about 2.5–4 for recurring characters). This is an assumption; failure rates aren't published by vendors.

| | **A: Own system** | **B: Video platform** |
|---|---|---|
| **Cash cost per episode (with failures)** | **$0.50–1.50** (LLM $0.30–0.60, ElevenLabs about $0.40–0.60, misc. $0.05) *(est.)*. About $0.30–0.70 if free SILMA voices are good enough. | Visuals: 300 s × $0.08–0.10/s × 3 = **$72–90**; at 1080p or with a 4× failure rate, **$100–180**. Plus voice about $0.50, plus a lip-sync pass (cost not verified). **About $75–180** *(est.)* |
| **Monthly, 10 episodes** | **About $25–40** (ElevenLabs Creator $22 + LLM about $5) | **About $750–1,800** (pay-as-you-go). A big subscription such as Kling Ultra at $180 ⚠️ covers only part of this, at a lower-quality mode. |
| **Monthly, 30 episodes** | **About $35–60** (ElevenLabs API pay-as-you-go about $15 + LLM about $15) | **About $2,250–5,400** |
| **One-time setup cost** | About $10–35 cash, plus **4–8 weeks** of your time (characters, rigs, building and testing the pipeline) | Almost none: a few days to learn the tools |
| **Visual quality** | Clean, flat 2D cartoon with limited motion. Quality depends on the character art. | Richer motion and lighting, but style flicker, artifacts and drift between clips |
| **Character consistency** | **Guaranteed**: the same art in every frame | **Moderate**: at most 3 references per clip; drifts over 40+ clips |
| **Arabic voice quality** | Same as B if ElevenLabs is used. Free SILMA (MSA) may be good enough but is unproven for expressive children's speech. | ElevenLabs. The platforms' own Arabic speech is not evaluated by Google. |
| **Arabic lip-sync** | Automatic, approximate (Rhubarb phonetic mode). Acceptable for cartoons. | Needs a separate lip-sync step; weak with several characters talking |
| **Ongoing manual work** | **About 15–30 min per episode** (review and approve) | **About 3–8 h per episode** (prompting, choosing takes, re-generating, editing, syncing) *(est.)* |
| **Reliability** | High: deterministic, re-renderable, few external dependencies | Medium-low: model shutdowns, price changes, content-moderation rejections |
| **Can it run continuously?** | Yes | Only at a high cost per episode and with your time on every episode |

**Break-even:** Option B costs about $70–180 more per episode. At 10 episodes/month that's about **$700–1,800/month** more, plus about 30–70 hours of your time. Option A's setup pays for itself in the **first month** of production.

---

## 5. Exact stack for the recommended option (A)

| Role | Tool / service | Cost |
|---|---|---|
| Orchestration | Python CLI pipeline with file-based stages (on your laptop) | Free |
| Writing (Arabic MSA) | Claude Sonnet 5.5 API (writer + critic); Gemini free tier as an optional fallback | About $3–20/mo |
| Arabic voices | ElevenLabs (Creator $22/mo, or API at $0.08 per 1k characters); **SILMA TTS** evaluated as the free replacement | $0–22/mo |
| Lip-sync | Rhubarb Lip Sync (phonetic mode) | Free |
| Character sheets (one-time) | Nano Banana 2.1 or Qwen-Image-Edit, curated by you | About $5–15 |
| Rig layers (one-time) | Qwen-Image-Layered on rented GPU (RunPod/Modal), plus manual cleanup in Krita | About $5–20 + your time |
| Backgrounds and props | Cloudflare Workers AI FLUX.1-schnell (free tier), reused from a library | Free |
| Render | Remotion (individual license) + FFmpeg | Free |
| Subtitles and QC | FFmpeg filters, faster-whisper (Arabic), small vision-LLM check | About $0.05/episode |
| Review | Output folder (Drive) + notification; you upload manually | Free |

---

## 6. Recommendation

**Choose Option A: build our own system.** It costs about 50–100× less per episode, guarantees character consistency, and needs about 20 minutes of your time per episode instead of hours. Using a video platform directly only makes sense if you want a cinematic look badly enough to pay about $75–180 per episode and edit every episode yourself. That doesn't fit the goal of a continuous, low-cost, hands-off system.

**Risk control before committing more time.** Build a cheap 1–2 week proof first:
1. One character rig.
2. A 60-second Arabic test scene.
3. ElevenLabs vs SILMA voices, compared side by side.
4. Rhubarb lip-sync on Arabic audio.

If the Arabic voice and the puppet look are acceptable to you, proceed to the full pipeline. If not, stop with only about $10–30 spent.
