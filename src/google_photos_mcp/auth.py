"""OAuth2 authentication for Google Photos API.

First-time setup:
1. Create OAuth credentials at https://console.cloud.google.com/apis/credentials
2. Enable "Photos Library API" at https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com
3. Download the OAuth client JSON and save as ~/.config/google-photos-mcp/oauth.json
4. Run: google-photos-auth
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]

CONFIG_DIR = Path(os.environ.get(
    "GOOGLE_PHOTOS_CONFIG_DIR",
    os.path.join(os.path.expanduser("~"), ".config", "google-photos-mcp"),
))
OAUTH_PATH = CONFIG_DIR / "oauth.json"
CREDENTIALS_PATH = CONFIG_DIR / "credentials.json"


def get_credentials() -> Credentials:
    """Load or refresh OAuth2 credentials.

    Returns valid credentials, refreshing if needed.
    Raises FileNotFoundError if oauth.json is missing and no credentials cached.
    """
    creds = None

    if CREDENTIALS_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(CREDENTIALS_PATH), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)
        return creds

    if not OAUTH_PATH.exists():
        raise FileNotFoundError(
            f"OAuth client file not found at {OAUTH_PATH}\n"
            "Download it from Google Cloud Console → APIs & Services → Credentials\n"
            "and save as: " + str(OAUTH_PATH)
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_PATH), SCOPES)
    creds = flow.run_local_server(port=8085)
    _save_credentials(creds)
    return creds


def _save_credentials(creds: Credentials) -> None:
    """Save credentials to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes and list(creds.scopes),
    }
    CREDENTIALS_PATH.write_text(json.dumps(data, indent=2))
    os.chmod(str(CREDENTIALS_PATH), 0o600)


def main() -> None:
    """Run interactive OAuth2 flow."""
    print("Google Photos MCP — OAuth2 Setup")
    print("=" * 40)
    print(f"Config dir: {CONFIG_DIR}")
    print(f"OAuth file: {OAUTH_PATH}")
    print()

    if not OAUTH_PATH.exists():
        print(f"ERROR: OAuth client file not found at {OAUTH_PATH}")
        print()
        print("Steps:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Create OAuth 2.0 Client ID (Desktop app)")
        print("3. Download the JSON file")
        print(f"4. Save it as: {OAUTH_PATH}")
        print()
        print("Also enable Photos Library API:")
        print("https://console.cloud.google.com/apis/library/photoslibrary.googleapis.com")
        sys.exit(1)

    try:
        creds = get_credentials()
        print(f"Authentication successful!")
        print(f"Credentials saved to: {CREDENTIALS_PATH}")
        print(f"Token valid: {creds.valid}")
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)
