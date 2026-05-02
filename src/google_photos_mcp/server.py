"""Google Photos MCP Server.

Exposes Google Photos albums, media items, and search to Claude
via the Model Context Protocol (MCP).
"""

from __future__ import annotations

import json
import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from google_photos_mcp.photos_client import GooglePhotosClient

load_dotenv()

logger = logging.getLogger(__name__)


def _build_server() -> FastMCP:
    """Build the FastMCP server."""
    return FastMCP(
        "Google Photos",
        instructions=(
            "Access your Google Photos library. Browse albums, search photos by date "
            "or category, and view photo metadata including camera info and dimensions."
        ),
    )


mcp = _build_server()

_client: GooglePhotosClient | None = None


def _get_client() -> GooglePhotosClient:
    """Get or create the Google Photos client."""
    global _client
    if _client is None:
        _client = GooglePhotosClient()
    return _client


# ── Tools ───────────────────────────────────────────────────────


@mcp.tool()
def list_albums(
    page_size: int = 50,
    page_token: str = "",
) -> str:
    """List albums in your Google Photos library.

    Returns album names, photo counts, and IDs for further queries.

    Args:
        page_size: Number of albums to return (max 50).
        page_token: Pagination token from previous request.
    """
    try:
        client = _get_client()
        albums, next_token = client.list_albums(page_size, page_token)

        if not albums:
            return "No albums found in your Google Photos library."

        results = [a.to_dict() for a in albums]
        response: dict = {"total_returned": len(results), "albums": results}
        if next_token:
            response["next_page_token"] = next_token
        return json.dumps(response, indent=2)
    except FileNotFoundError as e:
        return f"Setup required: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_album(album_id: str) -> str:
    """Get details of a specific album.

    Args:
        album_id: The album ID (from list_albums).
    """
    try:
        client = _get_client()
        album = client.get_album(album_id)
        return json.dumps(album.to_dict(), indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def list_media_items(
    page_size: int = 25,
    page_token: str = "",
) -> str:
    """List recent media items (photos/videos) in your library.

    Returns filenames, dates, dimensions, and camera info.

    Args:
        page_size: Number of items to return (max 100).
        page_token: Pagination token from previous request.
    """
    try:
        client = _get_client()
        items, next_token = client.list_media_items(page_size, page_token)

        if not items:
            return "No media items found."

        results = [item.to_dict() for item in items]
        response: dict = {"total_returned": len(results), "media_items": results}
        if next_token:
            response["next_page_token"] = next_token
        return json.dumps(response, indent=2)
    except FileNotFoundError as e:
        return f"Setup required: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_media_item(media_item_id: str) -> str:
    """Get full details of a specific photo or video.

    Returns filename, dimensions, camera info, creation date, and Google Photos URL.

    Args:
        media_item_id: The media item ID (from list_media_items or search).
    """
    try:
        client = _get_client()
        item = client.get_media_item(media_item_id)
        return json.dumps(item.to_dict(), indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def search_photos(
    date_start: str = "",
    date_end: str = "",
    category: str = "",
    media_type: str = "",
    page_size: int = 25,
    page_token: str = "",
) -> str:
    """Search for photos and videos with filters.

    You can combine multiple filters. At least one filter should be provided.

    Args:
        date_start: Start date in YYYY-MM-DD format (e.g. "2024-01-01").
        date_end: End date in YYYY-MM-DD format (e.g. "2024-12-31").
        category: Content category filter. Options: LANDSCAPES, RECEIPTS,
            CITYSCAPES, LANDMARKS, SELFIES, PEOPLE, PETS, WEDDINGS,
            BIRTHDAYS, TRAVEL, ANIMALS, FOOD, SPORT, NIGHT,
            PERFORMANCES, WHITEBOARDS, SCREENSHOTS, UTILITY.
        media_type: Type filter — "PHOTO" or "VIDEO" (default: all).
        page_size: Number of results (max 100).
        page_token: Pagination token from previous request.
    """
    try:
        categories = [category] if category else None
        client = _get_client()
        items, next_token = client.search_media_items(
            date_start=date_start,
            date_end=date_end,
            content_categories=categories,
            media_type=media_type,
            page_size=page_size,
            page_token=page_token,
        )

        if not items:
            return "No matching media items found."

        results = [item.to_dict() for item in items]
        response: dict = {"total_returned": len(results), "media_items": results}
        if next_token:
            response["next_page_token"] = next_token
        return json.dumps(response, indent=2)
    except FileNotFoundError as e:
        return f"Setup required: {e}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def list_album_photos(
    album_id: str,
    page_size: int = 25,
    page_token: str = "",
) -> str:
    """List all photos/videos in a specific album.

    Args:
        album_id: The album ID (from list_albums).
        page_size: Number of items to return (max 100).
        page_token: Pagination token from previous request.
    """
    try:
        client = _get_client()
        items, next_token = client.list_album_media_items(album_id, page_size, page_token)

        if not items:
            return "No media items found in this album."

        results = [item.to_dict() for item in items]
        response: dict = {"total_returned": len(results), "media_items": results}
        if next_token:
            response["next_page_token"] = next_token
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def search_by_date(
    year: int,
    month: int = 0,
    day: int = 0,
    page_size: int = 25,
    page_token: str = "",
) -> str:
    """Search for photos from a specific date or period.

    Provide year only for a full year, year+month for a month, or year+month+day for a day.

    Args:
        year: Year (e.g. 2024).
        month: Month (1-12, optional — 0 for whole year).
        day: Day (1-31, optional — 0 for whole month).
        page_size: Number of results (max 100).
        page_token: Pagination token.
    """
    try:
        if month == 0:
            start = f"{year}-01-01"
            end = f"{year}-12-31"
        elif day == 0:
            start = f"{year}-{month:02d}-01"
            if month == 12:
                end = f"{year}-12-31"
            else:
                end = f"{year}-{month + 1:02d}-01"
        else:
            start = f"{year}-{month:02d}-{day:02d}"
            end = start

        client = _get_client()
        items, next_token = client.search_media_items(
            date_start=start,
            date_end=end,
            page_size=page_size,
            page_token=page_token,
        )

        if not items:
            return f"No photos found for {start}" + (f" to {end}" if end != start else "") + "."

        results = [item.to_dict() for item in items]
        response: dict = {"total_returned": len(results), "media_items": results}
        if next_token:
            response["next_page_token"] = next_token
        return json.dumps(response, indent=2)
    except Exception as e:
        return f"Error: {e}"


def main() -> None:
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")
