"""Google Photos API client.

Wraps the Google Photos Library API for use by the MCP server.
API reference: https://developers.google.com/photos/library/reference/rest
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from googleapiclient.discovery import build

from google_photos_mcp.auth import get_credentials

logger = logging.getLogger(__name__)


@dataclass
class MediaItem:
    """A Google Photos media item (photo or video)."""

    id: str
    filename: str
    mime_type: str
    description: str = ""
    creation_time: str = ""
    width: int = 0
    height: int = 0
    base_url: str = ""
    product_url: str = ""
    camera_make: str = ""
    camera_model: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MediaItem:
        metadata = data.get("mediaMetadata", {})
        photo_meta = metadata.get("photo", {})
        return cls(
            id=data.get("id", ""),
            filename=data.get("filename", ""),
            mime_type=data.get("mimeType", ""),
            description=data.get("description", ""),
            creation_time=metadata.get("creationTime", ""),
            width=int(metadata.get("width", 0)),
            height=int(metadata.get("height", 0)),
            base_url=data.get("baseUrl", ""),
            product_url=data.get("productUrl", ""),
            camera_make=photo_meta.get("cameraMake", ""),
            camera_model=photo_meta.get("cameraModel", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "creation_time": self.creation_time,
            "dimensions": f"{self.width}x{self.height}",
        }
        if self.description:
            result["description"] = self.description
        if self.camera_make or self.camera_model:
            result["camera"] = f"{self.camera_make} {self.camera_model}".strip()
        if self.product_url:
            result["product_url"] = self.product_url
        return result


@dataclass
class Album:
    """A Google Photos album."""

    id: str
    title: str
    media_items_count: int = 0
    cover_photo_base_url: str = ""
    product_url: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Album:
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            media_items_count=int(data.get("mediaItemsCount", 0)),
            cover_photo_base_url=data.get("coverPhotoBaseUrl", ""),
            product_url=data.get("productUrl", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "media_items_count": self.media_items_count,
            "product_url": self.product_url,
        }


class GooglePhotosClient:
    """Client for the Google Photos Library API."""

    def __init__(self) -> None:
        self._service = None

    def _get_service(self):
        if self._service is None:
            creds = get_credentials()
            self._service = build("photoslibrary", "v1", credentials=creds, static_discovery=False)
        return self._service

    def list_albums(self, page_size: int = 50, page_token: str = "") -> tuple[list[Album], str]:
        """List albums in the user's library.

        Returns (albums, next_page_token).
        """
        service = self._get_service()
        kwargs: dict[str, Any] = {"pageSize": min(page_size, 50)}
        if page_token:
            kwargs["pageToken"] = page_token

        response = service.albums().list(**kwargs).execute()
        albums = [Album.from_api(a) for a in response.get("albums", [])]
        return albums, response.get("nextPageToken", "")

    def get_album(self, album_id: str) -> Album:
        """Get a specific album by ID."""
        service = self._get_service()
        data = service.albums().get(albumId=album_id).execute()
        return Album.from_api(data)

    def list_media_items(
        self,
        page_size: int = 25,
        page_token: str = "",
    ) -> tuple[list[MediaItem], str]:
        """List media items in the library.

        Returns (items, next_page_token).
        """
        service = self._get_service()
        kwargs: dict[str, Any] = {"pageSize": min(page_size, 100)}
        if page_token:
            kwargs["pageToken"] = page_token

        response = service.mediaItems().list(**kwargs).execute()
        items = [MediaItem.from_api(m) for m in response.get("mediaItems", [])]
        return items, response.get("nextPageToken", "")

    def get_media_item(self, media_item_id: str) -> MediaItem:
        """Get a specific media item by ID."""
        service = self._get_service()
        data = service.mediaItems().get(mediaItemId=media_item_id).execute()
        return MediaItem.from_api(data)

    def search_media_items(
        self,
        album_id: str = "",
        date_start: str = "",
        date_end: str = "",
        content_categories: list[str] | None = None,
        media_type: str = "",
        page_size: int = 25,
        page_token: str = "",
    ) -> tuple[list[MediaItem], str]:
        """Search for media items with filters.

        Args:
            album_id: Filter by album ID.
            date_start: Start date (YYYY-MM-DD).
            date_end: End date (YYYY-MM-DD).
            content_categories: Filter by content category
                (LANDSCAPES, RECEIPTS, CITYSCAPES, LANDMARKS, SELFIES,
                 PEOPLE, PETS, WEDDINGS, BIRTHDAYS, TRAVEL, ANIMALS,
                 FOOD, SPORT, NIGHT, PERFORMANCES, WHITEBOARDS, SCREENSHOTS, UTILITY).
            media_type: ALL_MEDIA, PHOTO, or VIDEO.
            page_size: Number of results per page (max 100).
            page_token: Token for pagination.

        Returns (items, next_page_token).
        """
        service = self._get_service()
        body: dict[str, Any] = {"pageSize": min(page_size, 100)}

        if album_id:
            body["albumId"] = album_id

        if page_token:
            body["pageToken"] = page_token

        filters: dict[str, Any] = {}

        if date_start or date_end:
            date_filter: dict[str, Any] = {}
            ranges: list[dict[str, Any]] = []
            range_entry: dict[str, Any] = {}

            if date_start:
                parts = date_start.split("-")
                range_entry["startDate"] = {
                    "year": int(parts[0]),
                    "month": int(parts[1]),
                    "day": int(parts[2]),
                }
            if date_end:
                parts = date_end.split("-")
                range_entry["endDate"] = {
                    "year": int(parts[0]),
                    "month": int(parts[1]),
                    "day": int(parts[2]),
                }

            ranges.append(range_entry)
            date_filter["ranges"] = ranges
            filters["dateFilter"] = date_filter

        if content_categories:
            filters["contentFilter"] = {
                "includedContentCategories": content_categories,
            }

        if media_type:
            filters["mediaTypeFilter"] = {"mediaTypes": [media_type]}

        if filters:
            body["filters"] = filters

        response = service.mediaItems().search(body=body).execute()
        items = [MediaItem.from_api(m) for m in response.get("mediaItems", [])]
        return items, response.get("nextPageToken", "")

    def list_album_media_items(
        self,
        album_id: str,
        page_size: int = 25,
        page_token: str = "",
    ) -> tuple[list[MediaItem], str]:
        """List media items in a specific album."""
        return self.search_media_items(
            album_id=album_id,
            page_size=page_size,
            page_token=page_token,
        )
