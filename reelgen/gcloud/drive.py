"""Google Drive v3 over REST using an OAuth refresh token (scope: drive.file, so the app
only sees files it created). Used by the pipeline (upload, cleanup) and the publisher (download)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

import requests

from .. import config

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
SCOPE = "https://www.googleapis.com/auth/drive.file"

_token: Optional[tuple[str, float]] = None


def _access_token() -> str:
    global _token
    if _token and _token[1] > time.time() + 60:
        return _token[0]
    if not (config.GOOGLE_CLIENT_ID and config.GOOGLE_CLIENT_SECRET and config.GOOGLE_REFRESH_TOKEN):
        raise RuntimeError("Google Drive credentials are not set (GOOGLE_CLIENT_ID / SECRET / REFRESH_TOKEN)")
    r = requests.post(TOKEN_URL, data={
        "client_id": config.GOOGLE_CLIENT_ID,
        "client_secret": config.GOOGLE_CLIENT_SECRET,
        "refresh_token": config.GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Google token refresh failed: {r.status_code} {r.text[:200]}")
    j = r.json()
    _token = (j["access_token"], time.time() + j.get("expires_in", 3600))
    return _token[0]


def _h() -> dict:
    return {"Authorization": f"Bearer {_access_token()}"}


def _ok(r: requests.Response) -> requests.Response:
    if r.status_code >= 300:
        raise RuntimeError(f"Drive API {r.request.method} {r.url} -> {r.status_code}: {r.text[:300]}")
    return r


def folder_id() -> str:
    q = (f"name = '{config.DRIVE_FOLDER_NAME}' and mimeType = 'application/vnd.google-apps.folder' "
         "and trashed = false")
    files = _ok(requests.get(f"{API}/files", headers=_h(), params={"q": q, "fields": "files(id)"}, timeout=30)).json()["files"]
    if files:
        return files[0]["id"]
    meta = {"name": config.DRIVE_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"}
    return _ok(requests.post(f"{API}/files", headers=_h(), json=meta, timeout=30)).json()["id"]


def upload(path: Path, name: str, mime: str = "video/mp4", parent: Optional[str] = None,
           description: str = "") -> dict:
    parent = parent or folder_id()
    meta = {"name": name, "parents": [parent], "description": description}
    # resumable upload: works for any size
    init = _ok(requests.post(f"{UPLOAD}?uploadType=resumable&fields=id,webViewLink", headers={
        **_h(), "X-Upload-Content-Type": mime, "Content-Type": "application/json; charset=UTF-8"},
        data=json.dumps(meta), timeout=30))
    loc = init.headers["Location"]
    with open(path, "rb") as f:
        r = _ok(requests.put(loc, headers={**_h(), "Content-Type": mime}, data=f, timeout=600))
    return r.json()


def list_folder(parent: Optional[str] = None) -> list[dict]:
    parent = parent or folder_id()
    q = f"'{parent}' in parents and trashed = false"
    out, page = [], None
    while True:
        params = {"q": q, "fields": "nextPageToken, files(id,name,createdTime,mimeType,size)", "pageSize": 100}
        if page:
            params["pageToken"] = page
        j = _ok(requests.get(f"{API}/files", headers=_h(), params=params, timeout=30)).json()
        out += j["files"]
        page = j.get("nextPageToken")
        if not page:
            return out


def delete(file_id: str) -> None:
    r = requests.delete(f"{API}/files/{file_id}", headers=_h(), timeout=30)
    if r.status_code not in (204, 404):
        _ok(r)


def download(file_id: str, dest: Path) -> Path:
    with requests.get(f"{API}/files/{file_id}", headers=_h(), params={"alt": "media"}, stream=True, timeout=600) as r:
        _ok(r)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return dest
