# Setting up ReelGen

About 30 minutes, once. Steps 2 to 4 make videos; step 5 posts them. There is no API bill:
the daily run uses your Claude plan.

## 1. Nothing to do for Claude
The daily run is a scheduled Claude Code session on your plan, so no Anthropic API key is needed.

## 2. Google Cloud (voice, narration check, Drive)
Use the same Google Cloud project you already set up for Text-to-Speech.

1. **APIs & Services → Library**: enable **Cloud Speech-to-Text API** and **Google Drive API**
   (Text-to-Speech is already on).
2. **APIs & Services → Credentials → your API key → API restrictions**: allow
   **Cloud Text-to-Speech API** and **Cloud Speech-to-Text API**. Rotate the key if it was ever pasted
   into a chat. You'll add it in step 4.
3. **OAuth consent screen**: User type External, app name "ReelGen", add your email as a test user,
   add the scope `.../auth/drive.file`. Then click **Publish app** so it's "In production".
   (In "Testing" mode Google expires the sign-in after 7 days.) Google will show an "unverified app"
   warning when you sign in; that's expected for your own app. Click Advanced → Continue.
4. **Credentials → Create credentials → OAuth client ID → Desktop app**. Note the client ID and secret.
5. On your laptop, from the repo folder:
   ```
   python scripts/google_auth.py <CLIENT_ID> <CLIENT_SECRET>
   ```
   Sign in with the Google account whose Drive should hold the videos. It prints a refresh token.
6. Keep the client ID, client secret and refresh token for step 4 and the publisher's `.env`.

## 3. Dashboard (GitHub Pages)
1. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Run **Actions → Deploy dashboard → Run workflow** once. The dashboard is then at
   `https://kevinandrin7-start.github.io/ReelGen/`.
3. Create a token for the dashboard: GitHub → Settings → Developer settings → **Fine-grained tokens**
   → Generate. Repository access: only ReelGen. Permissions: **Contents: Read and write**.
   Paste it into the dashboard's **Settings**. It stays in your browser.

The repository is public, so the backlog, scripts and research notes are visible to anyone. Videos
stay in your Drive. If you'd rather keep it private, make the repo private; GitHub Pages then needs a
paid GitHub plan.

## 4. Keys for the daily Claude session
The scheduled session runs in your Claude Code cloud environment ("Default"). Add the Google keys
there as environment variables: in the ReelGen project, open **Project settings → Environment**,
pick the cloud environment, click the gear, and add:

```
GOOGLE_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

Anyone, or any command, in a session on that environment can read these, so only use it for your
own work. Never paste the keys into a chat.

Then add a topic on the dashboard. The scheduled task makes the next queued topic every morning
at about 8 AM New York time. About 15 minutes later the video shows under **Waiting for your
approval** with a Drive link, the caption and the test results. If a run fails, the error appears
on the topic, and the run's session is listed in Claude Code.

## 5. Publisher on your Windows laptop
You need Python 3.12, Git and Google Chrome.

1. Clone the repo: `git clone https://github.com/kevinandrin7-start/ReelGen.git`
2. In PowerShell, in `ReelGen\publisher`:
   ```
   powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
   ```
   The first run creates `publisher\.env`. Fill it in (repo, a GitHub token with Contents read and
   write, and the same three Google values), then run the script again. It schedules the publisher
   for 10:00 and 19:00 every day.
3. Sign in once to the channel's accounts (not your personal ones):
   ```
   .\.venv\Scripts\python.exe publish.py login
   ```
   This opens a separate Chrome profile just for ReelGen. Sign in to Instagram and YouTube there,
   then press Enter in the terminal.
   The publisher only posts from the accounts named in `publisher\.env`: `YOUTUBE_HANDLE`
   (`@BrainBytesDaily-q9h`) and `INSTAGRAM_HANDLE` (`brain.bytesdaily`). Before every upload it checks
   which account Chrome is signed in to, and if it's a different one it stops without posting.
4. Approve a video on the dashboard, then test without publishing:
   ```
   .\.venv\Scripts\python.exe publish.py run --dry-run --max 1
   ```
   It fills everything in and stops before Publish/Share, saving screenshots in
   `publisher\screenshots\`. When that looks right, the scheduled runs post for real.

The laptop must be on and signed in at the scheduled times; a missed run happens when it next wakes.
If a site changes its layout and a step fails, the video stays approved, the error and a screenshot
are saved, and it's retried on the next run.

## Changing things
- Voice, speed, length, Drive limits: environment variables in `reelgen/config.py`.
- What the daily session does: [ROUTINE.md](ROUTINE.md).
- How a word is pronounced: `config/pronunciations.json`.
- Schedule: ask Claude to change the "ReelGen daily video" scheduled task; the publisher's times
  are in `publisher/setup_windows.ps1`.
