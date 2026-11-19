# Daily ReelGen run (for the scheduled Claude session)

You are running ReelGen's daily production on Kevin's Claude plan. You do the Researcher, Scripter
and Director work yourself; the `python -m reelgen` commands do the voice, video, testing, Google
Drive upload and backlog updates. Make **one** video, then stop. Never post anything to Instagram
or YouTube; Kevin approves videos on the dashboard and his laptop publishes them.

## 0. Set up
```bash
cd ReelGen 2>/dev/null || cd reelgen 2>/dev/null || git clone https://github.com/kevinandrin7-start/ReelGen.git && cd ReelGen
git checkout main && git pull --rebase origin main
pip install -q -r requirements.txt
git config user.name "reelgen-bot"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
export REELGEN_GIT_PUSH=1
```
Check that `ffmpeg` runs and that `GOOGLE_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and
`GOOGLE_REFRESH_TOKEN` are set (check they exist; never print their values). If any is missing,
stop and say which one.

## 1. Take the next topic
```bash
python -m reelgen start
```
- Exit 5 (`queue_empty`) or 2 (`drive_full`): nothing to make today. Stop and say why.
- Exit 0: note `topic_id`, `title`, `notes` and `run_dir` from the output.

If anything below fails in a way you can't fix, run
`python -m reelgen fail <topic_id> "<short reason>"` and stop. The topic is retried tomorrow.

## 2. Researcher
Run `python -m reelgen brief research` and follow those instructions. Use web search and web
fetch (about 4-6 searches and 2-4 pages; prefer official docs, original papers and reputable
engineering sources). Follow Kevin's `notes` for the topic. Write:
- `<run_dir>/research_notes.md`: your notes, with source URLs
- `<run_dir>/research.json`: matching the schema in the brief, every fact with its source URL

## 3. Scripter
Run `python -m reelgen brief script` and follow it exactly: 5 lines (hook, problem, define,
steps, payoff), 65-80 words in total, beginner-friendly and technically accurate, nothing that
isn't in your research. `spoken` must be the same words as `narration`, with acronyms written the
way they're said (use the pronunciation dictionary in the brief). Write `<run_dir>/script.json`.

## 4. Director
Run `python -m reelgen brief plan` and follow it. Keep every on-screen text within its character
limit. Write `<run_dir>/scene_plan.json`.

## 5. Check before rendering
```bash
python -m reelgen validate <run_dir>
python -m reelgen preview <run_dir>
```
Fix every problem and any length warnings. Open `<run_dir>/preview.png` and look at it: text
should fit its cards, nothing should overlap or be cut off, and the icons should match the ideas.
Adjust `scene_plan.json` and preview again if needed (at most 3 rounds).

## 6. Make the video
```bash
python -m reelgen finish <topic_id>
```
- Exit 0: done. It uploaded to Drive and marked the topic "ready" on the dashboard.
- Exit 3 (`too_long`): the narration doesn't fit 30 seconds. Shorten `script.json` (keep it
  accurate; about 70 words), update `scene_plan.json` if the steps changed, validate, finish again.
- Exit 4 (`narration_check_failed`): Google Speech-to-Text heard some words differently. Look at
  `misheard_words` and the transcript. For words the voice likely mispronounced (technical terms,
  acronyms, names), write `<run_dir>/respellings.json` mapping the word as written in the script
  to a spelling the voice will say correctly, e.g. `{"Kubernetes": "koo-ber-net-eez", "LLMs": "L L Ms"}`.
  Then run finish again. After two tries, run `python -m reelgen finish <topic_id> --accept`; the
  video is then marked "Needs your review" with the failed checks listed for Kevin.

## 7. Report
End with 2-3 sentences: the topic, the Drive link, whether all checks passed, and anything Kevin
should look at. If a respelling clearly worked, mention it, since it could go into
`config/pronunciations.json`.
