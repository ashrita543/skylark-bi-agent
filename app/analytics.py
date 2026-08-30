"""Deterministic business analytics for the Skylark BI agent."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Analytics:
    """Collection of deterministic BI calculations."""

    @staticmethod
    def get_current_quarter() -> str:
        today = date.today()
        quarter = (today.month - 1) // 3 + 1
        return f"Q{quarter} {today.year}"

    @staticmethod
    def get_quarter_date_range(year: int, quarter: int) -> Tuple[date, date]:
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        start_date = date(year, start_month, 1)
        if end_month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, end_month + 1, 1)
            end_date = date(end_date.year, end_date.month - 1, 31)
        return start_date, end_date

    @staticmethod
    def filter_by_quarter(deals: List[Dict[str, Any]], year: Optional[int] = None, quarter: Optional[int] = None) -> List[Dict[str, Any]]:
        if not deals:
            return []
        if year is None:
            year = date.today().year
        if quarter is None:
            quarter = (date.today().month - 1) // 3 + 1

        start_date, end_date = Analytics.get_quarter_date_range(year, quarter)
        filtered: List[Dict[str, Any]] = []

        for deal in deals:
            deal_date = deal.get("close_date") or deal.get("tentative_close_date")
            if isinstance(deal_date, datetime):
                candidate = deal_date.date()
            elif isinstance(deal_date, str):
                try:
                    candidate = datetime.fromisoformat(deal_date).date()
                except ValueError:
                    candidate = None
            else:
                candidate = None

            if candidate and start_date <= candidate <= end_date:
                filtered.append(deal)

        return filtered

    @staticmethod
    def calculate_total_pipeline(deals: List[Dict[str, Any]]) -> Tuple[float, int]:
        total = 0.0
        count = 0
        for deal in deals:
            value = deal.get("deal_value")
            if value is not None and isinstance(value, (int, float)):
                total += float(value)
                count += 1
        return total, count

    @staticmethod
    def calculate_active_pipeline(deals: List[Dict[str, Any]]) -> Tuple[float, int]:
        active_statuses = {"Open", "In Progress", "On Hold"}
        total = 0.0
        count = 0
        for deal in deals:
            status = deal.get("deal_status")
            value = deal.get("deal_value")
            if value is None:
                continue
            if status in active_statuses or status is None:
                total += float(value)
                count += 1
        return total, count

    @staticmethod
    def pipeline_by_sector(deals: List[Dict[str, Any]]) -> Dict[str, Tuple[float, int]]:
        sectors: Dict[str, Tuple[float, int]] = {}
        for deal in deals:
            sector = deal.get("sector") or "Unknown"
            value = deal.get("deal_value")
            if value is None or not isinstance(value, (int, float)):
                continue
            if sector not in sectors:
                sectors[sector] = (0.0, 0)
            current_total, current_count = sectors[sector]
            sectors[sector] = (current_total + float(value), current_count + 1)
        return sectors

    @staticmethod
    def pipeline_by_stage(deals: List[Dict[str, Any]]) -> Dict[str, Tuple[float, int]]:
        stages: Dict[str, Tuple[float, int]] = {}
        for deal in deals:
            stage = deal.get("deal_stage") or "Unknown"
            value = deal.get("deal_value")
            if value is None or not isinstance(value, (int, float)):
                continue
            if stage not in stages:
                stages[stage] = (0.0, 0)
            current_total, current_count = stages[stage]
            stages[stage] = (current_total + float(value), current_count + 1)
        return stages

    @staticmethod
    def calculate_average_deal_size(deals: List[Dict[str, Any]]) -> Optional[float]:
        total, count = Analytics.calculate_total_pipeline(deals)
        if count == 0:
            return None
        return total / count

    @staticmethod
    def calculate_weighted_pipeline(deals: List[Dict[str, Any]]) -> Tuple[float, int]:
        weighted_total = 0.0
        count = 0
        for deal in deals:
            value = deal.get("deal_value")
            probability = deal.get("probability")
            if value is None or probability is None:
                continue
            try:
                weighted_total += float(value) * float(probability)
                count += 1
            except (TypeError, ValueError):
                continue
        return weighted_total, count

    @staticmethod
    def count_deals_by_status(deals: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for deal in deals:
            status = deal.get("deal_status") or "Unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts

    @staticmethod
    def count_work_orders_by_status(work_orders: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for wo in work_orders:
            status = wo.get("execution_status") or "Unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts

    @staticmethod
    def count_active_work_orders(work_orders: List[Dict[str, Any]]) -> int:
        active_statuses = {"In Progress", "Not Started", "On Hold"}
        return sum(1 for wo in work_orders if wo.get("execution_status") in active_statuses)

    @staticmethod
    def count_completed_work_orders(work_orders: List[Dict[str, Any]]) -> int:
        return sum(1 for wo in work_orders if wo.get("execution_status") == "Completed")

    @staticmethod
    def detect_delayed_work_orders(work_orders: List[Dict[str, Any]], reference_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if reference_date is None:
            reference_date = datetime.now()
        delayed: List[Dict[str, Any]] = []
        for wo in work_orders:
            status = wo.get("execution_status")
            if status in {"Completed", "Cancelled"}:
                continue
            end_date = wo.get("probable_end_date")
            if not end_date:
                continue
            if isinstance(end_date, str):
                try:
                    end_date = datetime.fromisoformat(end_date)
                except ValueError:
                    continue
            if end_date < reference_date:
                delayed.append(wo)
        return delayed

    @staticmethod
    def calculate_billed_value(work_orders: List[Dict[str, Any]]) -> Tuple[float, int]:
        total = 0.0
        count = 0
        for wo in work_orders:
            value = wo.get("billed_value")
            if value is not None and isinstance(value, (int, float)):
                total += float(value)
                count += 1
        return total, count

    @staticmethod
    def work_orders_by_sector(work_orders: List[Dict[str, Any]]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for wo in work_orders:
            sector = wo.get("sector") or "Unknown"
            counts[sector] = counts.get(sector, 0) + 1
        return counts

    @staticmethod
    def generate_leadership_summary(deals: List[Dict[str, Any]], work_orders: List[Dict[str, Any]], data_quality_issues: Optional[List[str]] = None) -> Dict[str, Any]:
        pipeline_value, pipeline_count = Analytics.calculate_total_pipeline(deals)
        active_pipeline, active_count = Analytics.calculate_active_pipeline(deals)
        weighted_pipeline, weighted_count = Analytics.calculate_weighted_pipeline(deals)
        avg_deal = Analytics.calculate_average_deal_size(deals)

        billed_total, billed_count = Analytics.calculate_billed_value(work_orders)
        active_wos = Analytics.count_active_work_orders(work_orders)
        completed_wos = Analytics.count_completed_work_orders(work_orders)
        delayed_wos = Analytics.detect_delayed_work_orders(work_orders)

        return {
            "pipeline": {
                "total_value": pipeline_value,
                "total_count": pipeline_count,
                "active_value": active_pipeline,
                "active_count": active_pipeline,
                "active_deal_count": active_count,
                "weighted_value": weighted_pipeline,
                "weighted_count": weighted_count,
                "average_deal_size": avg_deal,
            },
            "work_orders": {
                "total_billed": billed_total,
                "billed_count": billed_count,
                "active_count": active_wos,
                "completed_count": completed_wos,
                "delayed_count": len(delayed_wos),
            },
            "by_sector": {
                "pipeline": Analytics.pipeline_by_sector(deals),
                "work_orders": Analytics.work_orders_by_sector(work_orders),
            },
            "status_distribution": {
                "deals": Analytics.count_deals_by_status(deals),
                "work_orders": Analytics.count_work_orders_by_status(work_orders),
            },
            "data_quality_caveats": data_quality_issues or [],
        }
