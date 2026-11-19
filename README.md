# ReelGen

An agentic pipeline that turns a backlog of topics into 30-second vertical infographic explainer
videos with voice narration, and posts them to Instagram Reels and YouTube Shorts after you approve them.

**Dashboard → Researcher → Scripter → Director → Sound engineer → Editor → Tester → Google Drive → your approval → Publisher**

- [ARCHITECTURE.md](ARCHITECTURE.md): how it works, the agents, Drive rules, costs
- [SETUP.md](SETUP.md): one-time setup (API keys, Google, Pages, laptop publisher)

## Commands
```bash
pip install -r requirements.txt          # needs ffmpeg on PATH
python -m reelgen demo                   # offline sample render (no API keys needed)
python -m reelgen add "Vector databases" --notes "beginner angle"
python -m reelgen produce                # make the next queued topic (needs the keys in SETUP.md)
python -m reelgen cleanup                # apply the Google Drive rules
python -m pytest -q tests
```
