"""Read-only Monday.com GraphQL client."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from app.config import Config

logger = logging.getLogger(__name__)


class MondayAPIError(Exception):
    """Raised for Monday API failures."""


class MondayClient:
    """Minimal read-only client for Monday.com GraphQL API."""

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or Config.MONDAY_API_TOKEN
        self.api_url = "https://api.monday.com/v2"
        self.headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
        }
        self.timeout = Config.API_TIMEOUT_SECONDS
        self.max_retries = Config.MAX_API_RETRIES

    def _request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL request and return response data."""
        if not self.api_token:
            raise MondayAPIError("Monday.com API token not configured")

        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    json=payload,
                    headers=self.headers,
                    timeout=self.timeout,
                )

                if response.status_code == 401:
                    raise MondayAPIError("Authentication failed - invalid API token")
                if response.status_code == 403:
                    raise MondayAPIError("Access forbidden")
                if response.status_code == 429:
                    raise MondayAPIError("Rate limit exceeded")

                response.raise_for_status()
                data = response.json()

                if isinstance(data, dict) and "errors" in data:
                    message = data["errors"][0].get("message", "Unknown GraphQL error")
                    raise MondayAPIError(f"GraphQL error: {message}")

                return data.get("data", {}) if isinstance(data, dict) else {}
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise MondayAPIError("API timeout - request took too long")
            except requests.exceptions.ConnectionError:
                if attempt == self.max_retries - 1:
                    raise MondayAPIError("Cannot connect to Monday.com API")
            except requests.exceptions.RequestException as exc:
                if attempt == self.max_retries - 1:
                    raise MondayAPIError(f"API request failed: {exc}")

        raise MondayAPIError("Unexpected request failure")

    def get_board_items(self, board_id: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Return all items from a Monday board, handling pagination."""
        if not board_id:
            raise MondayAPIError("Board ID is missing")

        all_items: List[Dict[str, Any]] = []
        cursor: Optional[str] = None

        while True:
            query = """
                query GetBoardItems($boardId: ID!, $limit: Int!, $cursor: String) {
                  boards(ids: [$boardId]) {
                    items_page(limit: $limit, cursor: $cursor) {
                      cursor
                      items {
                        id
                        name
                        created_at
                        column_values {
                          id
                          text
                          value
                          type
                        }
                      }
                    }
                  }
                }
            """
            variables = {"boardId": board_id, "limit": min(limit, 500), "cursor": cursor}
            response = self._request(query, variables)

            boards = response.get("boards", [])
            if not boards:
                raise MondayAPIError(f"Board {board_id} not found")

            items_page = boards[0].get("items_page", {})
            items = items_page.get("items", [])
            all_items.extend(items)

            next_cursor = items_page.get("cursor")
            if not next_cursor:
                break
            cursor = next_cursor

        return all_items

    def get_board_columns(self, board_id: str) -> List[Dict[str, Any]]:
        """Fetch metadata for all columns on a board."""
        if not board_id:
            raise MondayAPIError("Board ID is missing")

        query = """
            query GetBoardColumns($boardId: ID!) {
              boards(ids: [$boardId]) {
                columns {
                  id
                  title
                  type
                  settings_str
                }
              }
            }
        """

        response = self._request(query, {"boardId": board_id})
        boards = response.get("boards", [])
        if not boards:
            raise MondayAPIError(f"Board {board_id} not found")
        return boards[0].get("columns", [])

    def test_connection(self) -> bool:
        """Check whether the configured token can query Monday.com."""
        if not self.api_token:
            logger.warning("No Monday.com API token configured")
            return False

        try:
            response = self._request("query { me { id name } }")
            return bool(response.get("me"))
        except MondayAPIError:
            return False
