# CLAUDE.md — GooglePhotosMCP

## Wat is dit project?
MCP server die Claude Code toegang geeft tot Google Photos via de officiële Photos Library API.
Python + FastMCP, OAuth2 authenticatie, read-only.

## Tech Stack
- **Taal:** Python 3.10+
- **Framework:** FastMCP (Anthropic MCP SDK)
- **API:** Google Photos Library API (REST, `google-api-python-client`)
- **Auth:** OAuth2 via `google-auth-oauthlib`
- **Transport:** Stdio (Claude Code integratie)

## Structuur
```
src/google_photos_mcp/
├── __init__.py
├── auth.py          — OAuth2 flow, credential management
├── photos_client.py — Google Photos API wrapper
└── server.py        — FastMCP server, tool definities
```

## Credentials
- **Config dir:** `~/.config/google-photos-mcp/`
- **OAuth client:** `~/.config/google-photos-mcp/oauth.json` (van Google Cloud Console)
- **Tokens:** `~/.config/google-photos-mcp/credentials.json` (automatisch na auth)
- **Google Cloud project:** Claude-Gmail (personalgmailapi-492411)
- **Scope:** `photoslibrary.readonly`

## Tools (7)
| Tool | Functie |
|------|---------|
| `list_albums` | Albums in bibliotheek |
| `get_album` | Album details op ID |
| `list_media_items` | Recente foto's/video's |
| `get_media_item` | Detail van specifiek item |
| `search_photos` | Zoek op datum, categorie, mediatype |
| `list_album_photos` | Foto's in specifiek album |
| `search_by_date` | Zoek op jaar/maand/dag |

## Versioning
- Elke wijziging → versie +0.0.1 minimaal
- Codenaam-thema: **Beroemde fotografen**

## MCP Config
In `~/.claude/.mcp.json`:
```json
"google-photos": {
  "command": "/Users/christian/Documents/Gemini_Projects/GooglePhotosMCP/venv/bin/google-photos-mcp",
  "args": []
}
```

## Setup
```bash
cd /Users/christian/Documents/Gemini_Projects/GooglePhotosMCP
python3 -m venv venv
source venv/bin/activate
pip install -e .
google-photos-auth
```

## Regels
- **WhatIf Protocol:** verplicht vóór elke wijziging
- **Read-only:** deze MCP server wijzigt NOOIT foto's/albums
- **Geen foto-inhoud:** alleen metadata, geen pixels (API-beperking)
