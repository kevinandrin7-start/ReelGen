# Setting up ReelGen

About 30 minutes, once. Steps 1 to 4 make videos; step 5 posts them.

## 1. Anthropic API key
1. Go to console.anthropic.com → API keys → Create key.
2. Add billing and, to be safe, a monthly spend limit (for example $40).
3. In GitHub: **ReelGen → Settings → Secrets and variables → Actions → New repository secret**:
   `ANTHROPIC_API_KEY`.

Optional: under the **Variables** tab, add `REELGEN_MODEL` = `claude-sonnet-5-5` to roughly halve the cost.

## 2. Google Cloud (voice, narration check, Drive)
Use the same Google Cloud project you already set up for Text-to-Speech.

1. **APIs & Services → Library**: enable **Cloud Speech-to-Text API** and **Google Drive API**
   (Text-to-Speech is already on).
2. **APIs & Services → Credentials → your API key → API restrictions**: allow
   **Cloud Text-to-Speech API** and **Cloud Speech-to-Text API**. Rotate the key if it was ever pasted
   into a chat, then add it as the GitHub secret `GOOGLE_API_KEY`.
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
6. Add three GitHub secrets: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`.

## 3. Dashboard (GitHub Pages)
1. **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Run **Actions → Deploy dashboard → Run workflow** once. The dashboard is then at
   `https://kevinandrin7-start.github.io/ReelGen/`.
3. Create a token for the dashboard: GitHub → Settings → Developer settings → **Fine-grained tokens**
   → Generate. Repository access: only ReelGen. Permissions: **Contents: Read and write**,
   **Actions: Read and write**. Paste it into the dashboard's **Settings**. It stays in your browser.

The repository is public, so the backlog, scripts and research notes are visible to anyone. Videos
stay in your Drive. If you'd rather keep it private, make the repo private; Actions then uses your
free monthly minutes (about 3 minutes per video) and Pages needs a paid plan.

## 4. First video
1. Add a topic on the dashboard.
2. Click **Run now** (or wait for the daily run at 13:00 UTC, 8 AM New York time).
3. About 10 minutes later the video shows under **Waiting for your approval** with a Drive link,
   the caption and the test results. If a run fails, the error appears on the topic, and the full
   log is under the repo's **Actions** tab.

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
- Voice, speed, length, Drive limits, model: environment variables in `reelgen/config.py`.
- How a word is pronounced: `config/pronunciations.json`.
- Schedule: the `cron` lines in `.github/workflows/produce.yml` (UTC) and the times in
  `publisher/setup_windows.ps1`.
