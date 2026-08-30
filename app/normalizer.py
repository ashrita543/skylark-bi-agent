"""Normalization helpers for messy Monday.com exports."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Clean and normalize business data from Monday.com exports."""

    SECTOR_MAPPING = {
        "energy": "Energy",
        "powerline": "Powerline",
        "mining": "Mining",
        "manufacturing": "Manufacturing",
        "telecommunications": "Telecommunications",
        "utilities": "Utilities",
        "utility": "Utilities",
        "power": "Powerline",
        "mines": "Mining",
    }

    DEAL_STATUS_MAPPING = {
        "open": "Open",
        "on hold": "On Hold",
        "on-hold": "On Hold",
        "closed": "Closed",
        "won": "Won",
        "lost": "Lost",
        "qualified": "Qualified",
    }

    EXECUTION_STATUS_MAPPING = {
        "completed": "Completed",
        "in progress": "In Progress",
        "in-progress": "In Progress",
        "not started": "Not Started",
        "not-started": "Not Started",
        "on hold": "On Hold",
        "on-hold": "On Hold",
        "cancelled": "Cancelled",
        "canceled": "Cancelled",
    }

    PROBABILITY_MAPPING = {
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
    }

    @staticmethod
    def normalize_string(value: Any, allow_empty: bool = False) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, (int, float)) and not pd.isna(value):
            value = str(value)
        if not isinstance(value, str):
            return None

        value = value.strip()
        if not value:
            return "" if allow_empty else None
        return value

    @staticmethod
    def normalize_date(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            text = value.strip()
            if not text or text.lower() in {"nan", "n/a", "na", "null"}:
                return None
            text = text.replace("T", " ").replace("Z", "")

            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%m-%d-%Y",
                "%d-%b-%y",
                "%d-%b-%Y",
                "%d %b %Y",
                "%b %d, %Y",
                "%B %d, %Y",
                "%d-%B-%Y",
                "%d %B %Y",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(text, fmt)
                except ValueError:
                    continue

            # Add a few loose variants for strings like 5-Jan-26 and Jan 5, 2026.
            try:
                return datetime.strptime(text, "%d-%b-%y")
            except ValueError:
                pass
            try:
                return datetime.strptime(text, "%b %d, %Y")
            except ValueError:
                pass
            try:
                return datetime.strptime(text, "%d %b %Y")
            except ValueError:
                pass

            logger.warning("Could not parse date value: %s", value)
            return None

        return None

    @staticmethod
    def normalize_numeric(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)) and not pd.isna(value):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned or cleaned.lower() in {"nan", "n/a", "na", "null"}:
                return None

            cleaned = cleaned.replace("(", "-").replace(")", "")
            cleaned = cleaned.replace("₹", "").replace("$", "").replace("€", "").replace("£", "").replace("¥", "")
            cleaned = cleaned.replace(",", "").replace(" ", "")
            cleaned = cleaned.strip()

            suffix_multiplier = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
            lower = cleaned.lower()
            for suffix, multiplier in suffix_multiplier.items():
                if lower.endswith(suffix):
                    try:
                        numeric_part = cleaned[:-1]
                        return float(numeric_part) * multiplier
                    except ValueError:
                        return None

            try:
                return float(cleaned)
            except ValueError:
                logger.warning("Could not parse numeric value: %s", value)
                return None

        return None

    @staticmethod
    def normalize_sector(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = DataNormalizer.normalize_string(value)
        if not normalized:
            return None
        lowered = normalized.lower()
        for key, standard in DataNormalizer.SECTOR_MAPPING.items():
            if lowered == key or key in lowered or lowered in key:
                return standard
        return normalized

    @staticmethod
    def normalize_probability(value: Optional[str]) -> Optional[float]:
        if value is None:
            return None
        normalized = DataNormalizer.normalize_string(value)
        if not normalized:
            return None
        lower = normalized.lower().strip()
        if lower in DataNormalizer.PROBABILITY_MAPPING:
            return DataNormalizer.PROBABILITY_MAPPING[lower]

        cleaned = normalized.replace("%", "").strip()
        numeric = DataNormalizer.normalize_numeric(cleaned)
        if numeric is None:
            return None
        numeric = max(0.0, min(1.0, numeric / 100 if numeric > 1 else numeric))
        return numeric

    @staticmethod
    def normalize_deal_status(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = DataNormalizer.normalize_string(value)
        if not normalized:
            return None
        lower = normalized.lower()
        for key, standard in DataNormalizer.DEAL_STATUS_MAPPING.items():
            if key in lower or lower in key:
                return standard
        return normalized

    @staticmethod
    def normalize_execution_status(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = DataNormalizer.normalize_string(value)
        if not normalized:
            return None
        lower = normalized.lower()
        for key, standard in DataNormalizer.EXECUTION_STATUS_MAPPING.items():
            if key in lower or lower in key:
                return standard
        return normalized

    @staticmethod
    def create_record_from_items(items: List[Dict[str, Any]], column_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for item in items:
            record: Dict[str, Any] = {
                "id": item.get("id"),
                "name": item.get("name"),
                "created_at": DataNormalizer.normalize_date(item.get("created_at")),
            }

            for col_value in item.get("column_values", []):
                col_id = col_value.get("id")
                if col_id not in column_mapping:
                    continue
                field_name = column_mapping[col_id]

                value = col_value.get("text")
                if value is None and isinstance(col_value.get("value"), dict):
                    value = col_value["value"].get("text") or col_value["value"].get("label")
                if value is None and isinstance(col_value.get("value"), (str, int, float)):
                    value = col_value.get("value")
                record[field_name] = value

            records.append(record)
        return records

    @staticmethod
    def get_data_quality_report(records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {
                "total_records": 0,
                "issues": ["No records found"],
                "missing_by_field": {},
            }

        field_names = list(records[0].keys())
        missing_by_field: Dict[str, Dict[str, Any]] = {}
        for field in field_names:
            missing_count = sum(1 for r in records if r.get(field) in (None, "", " "))
            if missing_count:
                missing_by_field[field] = {
                    "count": missing_count,
                    "percentage": round((missing_count / len(records)) * 100, 1),
                }

        issues = []
        if missing_by_field:
            issues.append(f"Missing values found in {len(missing_by_field)} fields")
        return {
            "total_records": len(records),
            "issues": issues,
            "missing_by_field": missing_by_field,
        }
