"""Environment configuration for Skylark Drones BI Agent."""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()


def _get_config_value(key: str, default: str = "") -> str:
    """Get config value from environment, with Streamlit secrets fallback."""
    # First try environment variable (set by .env or Streamlit Cloud)
    value = os.getenv(key)
    if value:
        return value
    
    # Then try Streamlit secrets (for local Streamlit testing with .streamlit/secrets.toml)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except (ImportError, AttributeError):
        pass
    
    return default


class Config:
    """Application configuration loaded from environment variables and Streamlit secrets."""

    MONDAY_API_TOKEN: str = _get_config_value("MONDAY_API_TOKEN")
    DEALS_BOARD_ID: str = _get_config_value("DEALS_BOARD_ID")
    WORK_ORDERS_BOARD_ID: str = _get_config_value("WORK_ORDERS_BOARD_ID")
    OPENAI_API_KEY: str = _get_config_value("OPENAI_API_KEY")
    OPENAI_MODEL: str = _get_config_value("OPENAI_MODEL", "gpt-4-turbo-preview")
    CACHE_EXPIRY_SECONDS: int = int(_get_config_value("CACHE_EXPIRY_SECONDS", "600"))
    MAX_API_RETRIES: int = int(_get_config_value("MAX_API_RETRIES", "3"))
    API_TIMEOUT_SECONDS: int = int(_get_config_value("API_TIMEOUT_SECONDS", "30"))

    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Return whether config is sufficient and list missing values."""
        missing: list[str] = []
        if not cls.MONDAY_API_TOKEN:
            missing.append("MONDAY_API_TOKEN")
        if not cls.DEALS_BOARD_ID:
            missing.append("DEALS_BOARD_ID")
        if not cls.WORK_ORDERS_BOARD_ID:
            missing.append("WORK_ORDERS_BOARD_ID")
        if not cls.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        return len(missing) == 0, missing

    @classmethod
    def get_safe_config_display(cls) -> dict:
        """Return config safe for display in the UI without exposing secrets."""
        return {
            "deals_board_id": cls.DEALS_BOARD_ID or "Not configured",
            "work_orders_board_id": cls.WORK_ORDERS_BOARD_ID or "Not configured",
            "cache_expiry_seconds": cls.CACHE_EXPIRY_SECONDS,
            "api_model": cls.OPENAI_MODEL,
        }
