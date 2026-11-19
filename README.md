# ReelGen

An agentic pipeline that turns a backlog of topics into 30-second vertical infographic explainer
videos with voice narration, and posts them to Instagram Reels and YouTube Shorts after you approve them.

**Dashboard → Researcher → Scripter → Director → Sound engineer → Editor → Tester → Google Drive → your approval → Publisher**

- [ARCHITECTURE.md](ARCHITECTURE.md): how it works, the agents, Drive rules, costs
- [SETUP.md](SETUP.md): one-time setup (Google, Pages, the daily Claude session, laptop publisher)
- [ROUTINE.md](ROUTINE.md): what the daily scheduled Claude session does

## Commands
```bash
pip install -r requirements.txt          # needs ffmpeg on PATH
python -m reelgen demo                   # offline sample render (no API keys needed)
python -m reelgen add "Vector databases" --notes "beginner angle"
python -m reelgen start | validate | preview | finish   # the daily session's steps (ROUTINE.md)
python -m reelgen produce                # API mode: all agents via the Claude API (needs ANTHROPIC_API_KEY)
python -m reelgen cleanup                # apply the Google Drive rules
python -m pytest -q tests
```
