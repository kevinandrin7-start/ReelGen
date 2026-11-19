"""Browser steps for YouTube Studio and Instagram web, using Playwright with your installed Chrome.

These sites change their pages often. Every step looks for the control a few different ways,
saves a screenshot when it fails, and `--dry-run` stops right before the final Publish/Share."""
from __future__ import annotations

import random
import re
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import Locator, Page, TimeoutError as PWTimeout

SHOTS = Path(__file__).resolve().parent / "screenshots"


class PostError(RuntimeError):
    pass


def pause(a: float = 0.8, b: float = 2.0) -> None:
    time.sleep(random.uniform(a, b))  # unhurried, human-paced


def first_visible(page: Page, *candidates: Locator, timeout: float = 15000) -> Locator:
    deadline = time.time() + timeout / 1000
    while time.time() < deadline:
        for loc in candidates:
            try:
                if loc.count() and loc.first.is_visible():
                    return loc.first
            except Exception:
                pass
        time.sleep(0.4)
    raise PWTimeout("none of the expected controls appeared")


def shot(page: Page, name: str) -> Path:
    SHOTS.mkdir(exist_ok=True)
    p = SHOTS / f"{time.strftime('%Y%m%d-%H%M%S')}-{name}.png"
    try:
        page.screenshot(path=str(p), full_page=True)
    except Exception:
        pass
    return p


def _type_into(page: Page, box: Locator, text: str) -> None:
    box.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line:
            page.keyboard.insert_text(line)
        if i < len(lines) - 1:
            page.keyboard.press("Shift+Enter")
    pause(0.4, 0.9)


# ------------------------------------------------------------------ YouTube --

CHANNEL_RE = re.compile(r"/channel/(UC[\w-]{22})")


def youtube_channel_id(page: Page, handle: str) -> str:
    """The channel ID (UC...) behind a handle such as @BrainBytesDaily-q9h."""
    page.goto(f"https://www.youtube.com/{handle}", wait_until="domcontentloaded")
    for sel in ('link[rel="canonical"]', 'meta[itemprop="url"]', 'meta[property="og:url"]'):
        try:
            loc = page.locator(sel).first
            val = loc.get_attribute("href" if sel.startswith("link") else "content", timeout=10000) or ""
        except Exception:
            continue
        m = CHANNEL_RE.search(val)
        if m:
            return m.group(1)
    raise PostError(f"could not find the YouTube channel {handle}; check YOUTUBE_HANDLE in publisher/.env")


def youtube_active_channel(page: Page) -> str:
    """The channel ID that YouTube Studio opens for the signed-in account."""
    page.goto("https://studio.youtube.com/", wait_until="domcontentloaded")
    if "accounts.google.com" in page.url:
        raise PostError("not signed in to YouTube; run `python publish.py login` first")
    page.wait_for_url(CHANNEL_RE, timeout=60000)
    return CHANNEL_RE.search(page.url).group(1)


def check_youtube_channel(page: Page, handle: str) -> str:
    """Make sure Chrome is posting as `handle`. Returns its channel ID, or raises PostError."""
    want = youtube_channel_id(page, handle)
    have = youtube_active_channel(page)
    if have != want:
        raise PostError(f"Chrome is signed in to YouTube channel {have}, not {handle} ({want}). In the ReelGen "
                        f"Chrome window, click the profile picture > Switch account > {handle}, then run again. "
                        "Nothing was posted.")
    return want


def post_youtube(page: Page, video: Path, title: str, description: str, dry_run: bool,
                 channel_id: str) -> Optional[str]:
    try:
        page.goto("https://www.youtube.com/upload", wait_until="domcontentloaded")
        if "accounts.google.com" in page.url:
            raise PostError("not signed in to YouTube; run `python publish.py login` first")
        page.wait_for_url(CHANNEL_RE, timeout=60000)
        if CHANNEL_RE.search(page.url).group(1) != channel_id:  # checked again right before uploading
            raise PostError(f"YouTube Studio opened channel {CHANNEL_RE.search(page.url).group(1)}, "
                            f"not {channel_id}. Nothing was posted.")
        page.locator('input[type="file"]').first.set_input_files(str(video))
        pause(3, 5)
        title_box = first_visible(page, page.locator("#title-textarea #textbox"),
                                  page.get_by_label(re.compile("title", re.I)).locator("[contenteditable]"), timeout=60000)
        _type_into(page, title_box, title[:100])
        desc_box = first_visible(page, page.locator("#description-textarea #textbox"),
                                 page.get_by_label(re.compile("description", re.I)).locator("[contenteditable]"))
        _type_into(page, desc_box, description[:4900])
        first_visible(page, page.locator('[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]'),
                      page.get_by_role("radio", name=re.compile("not made for kids", re.I))).click()
        pause()
        for _ in range(3):
            first_visible(page, page.locator("#next-button"), page.get_by_role("button", name="Next")).click()
            pause(1.2, 2.2)
        first_visible(page, page.locator('[name="PUBLIC"]'), page.get_by_role("radio", name="Public")).click()
        pause()
        link = None
        try:
            link = page.locator("a.ytcp-video-info, .video-url-fadeable a").first.get_attribute("href", timeout=10000)
        except Exception:
            pass
        if dry_run:
            shot(page, "youtube-dry-run")
            return link
        # wait until the upload itself has finished before publishing
        page.wait_for_function(
            "() => !/Uploading|Uploaded \\d+%/i.test(document.querySelector('ytcp-uploads-dialog')?.innerText || '')",
            timeout=15 * 60 * 1000)
        first_visible(page, page.locator("#done-button"), page.get_by_role("button", name=re.compile("publish|save", re.I))).click()
        first_visible(page, page.get_by_text(re.compile("Video published|published", re.I)), timeout=120000)
        pause(2, 3)
        return link
    except Exception as e:
        p = shot(page, "youtube-error")
        raise PostError(f"YouTube upload failed: {e} (screenshot: {p})") from e


# ---------------------------------------------------------------- Instagram --

def _click_text_button(page: Page, name: str, timeout: float = 20000) -> None:
    first_visible(page, page.get_by_role("button", name=name, exact=True),
                  page.locator(f'div[role="button"]:text-is("{name}")'),
                  page.get_by_text(name, exact=True), timeout=timeout).click()


IG_USER_JS = """async () => {
  try {
    const r = await fetch('/api/v1/accounts/current_user/?edit=true',
      { credentials: 'include', headers: { 'X-IG-App-ID': '936619743392459' } });
    if (!r.ok) return null;
    const j = await r.json();
    return (j.user && j.user.username) || null;
  } catch (e) { return null; }
}"""


def check_instagram_account(page: Page, handle: str) -> None:
    """Make sure Chrome is posting as `handle` on Instagram, or raise PostError."""
    want = handle.lstrip("@").lower()
    page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
    pause(3, 5)
    if "accounts/login" in page.url or page.locator('input[name="username"]').count():
        raise PostError("not signed in to Instagram; run `python publish.py login` first")
    have = page.evaluate(IG_USER_JS)
    if have is None:  # fall back to the Profile link in the side menu
        link = page.locator(f'a[href="/{want}/"]')
        have = want if link.count() else "an unknown account"
    if have.lower() != want:
        raise PostError(f"Chrome is signed in to Instagram as {have}, not @{want}. In the ReelGen Chrome window, "
                        f"switch to @{want}, then run again. Nothing was posted.")


def post_instagram(page: Page, video: Path, caption: str, dry_run: bool, handle: str) -> Optional[str]:
    try:
        check_instagram_account(page, handle)  # checked right before every upload
        first_visible(page, page.locator('svg[aria-label="New post"]'), page.locator('svg[aria-label="Create"]'),
                      page.get_by_role("link", name=re.compile("^(New post|Create)$"))).click()
        pause()
        try:  # newer layout opens a small menu with "Post"
            first_visible(page, page.get_by_role("link", name="Post"), page.get_by_text("Post", exact=True), timeout=4000).click()
            pause()
        except PWTimeout:
            pass
        page.locator('input[type="file"]').first.set_input_files(str(video))
        pause(3, 5)
        try:  # "Video posts are now shared as reels"
            _click_text_button(page, "OK", timeout=5000)
        except PWTimeout:
            pass
        try:  # keep the full 9:16 frame
            first_visible(page, page.locator('svg[aria-label="Select crop"]'), timeout=8000).click()
            pause(0.5, 1)
            first_visible(page, page.get_by_text("Original", exact=True), timeout=5000).click()
            pause(0.5, 1)
        except PWTimeout:
            pass
        _click_text_button(page, "Next")
        pause(1.5, 3)
        _click_text_button(page, "Next")
        pause(1.5, 3)
        box = first_visible(page, page.locator('div[aria-label="Write a caption..."]'),
                            page.locator('[contenteditable="true"][role="textbox"]'))
        _type_into(page, box, caption[:2150])
        if dry_run:
            shot(page, "instagram-dry-run")
            return None
        _click_text_button(page, "Share")
        first_visible(page, page.get_by_text(re.compile("(reel|post) has been shared|Reel shared", re.I)),
                      timeout=10 * 60 * 1000)
        pause(2, 3)
        return None
    except Exception as e:
        p = shot(page, "instagram-error")
        raise PostError(f"Instagram upload failed: {e} (screenshot: {p})") from e
