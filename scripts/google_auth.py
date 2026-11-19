"""One-time helper: get a Google Drive refresh token for ReelGen.

1. In Google Cloud Console, create an OAuth client of type "Desktop app".
2. Run:  python scripts/google_auth.py <CLIENT_ID> <CLIENT_SECRET>
3. Sign in with the Google account whose Drive should hold the videos and allow access.
4. Copy the printed refresh token into the GOOGLE_REFRESH_TOKEN secret (and publisher/.env).

The scope is drive.file: ReelGen can only see and delete files it created itself.
"""
import http.server
import json
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

SCOPE = "https://www.googleapis.com/auth/drive.file"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    client_id, client_secret = sys.argv[1], sys.argv[2]
    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                result["code"] = q["code"][0]
                msg = "ReelGen is connected to Google Drive. You can close this tab."
            else:
                msg = "Something went wrong. Check the terminal."
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(msg.encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening your browser. If it doesn't open, visit:\n" + url)
    webbrowser.open(url)
    t = threading.Thread(target=srv.handle_request)
    t.start()
    t.join(timeout=300)
    if "code" not in result:
        sys.exit("No authorization code received.")
    data = urllib.parse.urlencode({"code": result["code"], "client_id": client_id, "client_secret": client_secret,
                                   "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
    tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data=data))
    if "refresh_token" not in tok:
        sys.exit(f"No refresh token in response: {tok}")
    print("\nGOOGLE_REFRESH_TOKEN=" + tok["refresh_token"])


if __name__ == "__main__":
    main()
