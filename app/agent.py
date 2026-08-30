"""Query planning and orchestration for the BI agent."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app import prompts
from app.analytics import Analytics
from app.config import Config
from app.monday_client import MondayAPIError, MondayClient
from app.normalizer import DataNormalizer

logger = logging.getLogger(__name__)


class Agent:
    """Main orchestrator for question planning, data retrieval, and analytics."""

    def __init__(self, monday_client: Optional[MondayClient] = None):
        self.monday_client = monday_client or MondayClient()
        self.deals_cache: Optional[List[Dict[str, Any]]] = None
        self.work_orders_cache: Optional[List[Dict[str, Any]]] = None
        self.data_quality_issues: List[str] = []

    def fetch_and_normalize_deals(self, force_refresh: bool = False) -> Tuple[List[Dict[str, Any]], List[str]]:
        if self.deals_cache is not None and not force_refresh:
            return self.deals_cache, self.data_quality_issues

        issues: List[str] = []
        try:
            board_id = Config.DEALS_BOARD_ID
            if not board_id:
                raise MondayAPIError("DEALS_BOARD_ID not configured")

            items = self.monday_client.get_board_items(board_id)
            if not items:
                self.deals_cache = []
                return [], ["No deals found in the configured Deals board."]

            columns = self.monday_client.get_board_columns(board_id)
            column_mapping = {col["id"]: col["title"] for col in columns}
            records = DataNormalizer.create_record_from_items(items, column_mapping)

            normalized: List[Dict[str, Any]] = []
            for record in records:
                normalized.append(
                    {
                        "id": record.get("id"),
                        "name": DataNormalizer.normalize_string(record.get("name")),
                        "deal_name": DataNormalizer.normalize_string(record.get("Deal Name") or record.get("name")),
                        "owner": DataNormalizer.normalize_string(record.get("Owner code")),
                        "client": DataNormalizer.normalize_string(record.get("Client Code")),
                        "deal_status": DataNormalizer.normalize_deal_status(record.get("Deal Status")),
                        "close_date": DataNormalizer.normalize_date(record.get("Close Date (A)")),
                        "probability": DataNormalizer.normalize_probability(record.get("Closure Probability")),
                        "deal_value": DataNormalizer.normalize_numeric(record.get("Masked Deal value")),
                        "tentative_close_date": DataNormalizer.normalize_date(record.get("Tentative Close Date")),
                        "deal_stage": DataNormalizer.normalize_string(record.get("Deal Stage")),
                        "product": DataNormalizer.normalize_string(record.get("Product deal")),
                        "sector": DataNormalizer.normalize_sector(record.get("Sector/service")),
                    }
                )

            if any(r.get("deal_value") is None for r in normalized):
                missing_count = sum(1 for r in normalized if r.get("deal_value") is None)
                issues.append(f"{missing_count} deals are missing deal values and were excluded from totals.")
            if any(r.get("sector") is None for r in normalized):
                missing_count = sum(1 for r in normalized if r.get("sector") is None)
                issues.append(f"{missing_count} deals have missing or unrecognized sector values.")

            self.deals_cache = normalized
            self.data_quality_issues = issues
            return normalized, issues
        except MondayAPIError as exc:
            logger.error("Deals fetch failed: %s", exc)
            return [], [f"I couldn't retrieve the Deals board from Monday.com right now: {exc}"]

    def fetch_and_normalize_work_orders(self, force_refresh: bool = False) -> Tuple[List[Dict[str, Any]], List[str]]:
        if self.work_orders_cache is not None and not force_refresh:
            return self.work_orders_cache, self.data_quality_issues

        issues: List[str] = []
        try:
            board_id = Config.WORK_ORDERS_BOARD_ID
            if not board_id:
                raise MondayAPIError("WORK_ORDERS_BOARD_ID not configured")

            items = self.monday_client.get_board_items(board_id)
            if not items:
                self.work_orders_cache = []
                return [], ["No work orders found in the configured Work Orders board."]

            columns = self.monday_client.get_board_columns(board_id)
            column_mapping = {col["id"]: col["title"] for col in columns}
            records = DataNormalizer.create_record_from_items(items, column_mapping)

            normalized: List[Dict[str, Any]] = []
            for record in records:
                normalized.append(
                    {
                        "id": record.get("id"),
                        "name": DataNormalizer.normalize_string(record.get("name")),
                        "deal_name": DataNormalizer.normalize_string(record.get("Deal name masked") or record.get("name")),
                        "customer": DataNormalizer.normalize_string(record.get("Customer Name Code")),
                        "serial": DataNormalizer.normalize_string(record.get("Serial #")),
                        "nature_of_work": DataNormalizer.normalize_string(record.get("Nature of Work")),
                        "execution_status": DataNormalizer.normalize_execution_status(record.get("Execution Status")),
                        "delivery_date": DataNormalizer.normalize_date(record.get("Data Delivery Date")),
                        "probable_start_date": DataNormalizer.normalize_date(record.get("Probable Start Date")),
                        "probable_end_date": DataNormalizer.normalize_date(record.get("Probable End Date")),
                        "sector": DataNormalizer.normalize_sector(record.get("Sector")),
                        "type_of_work": DataNormalizer.normalize_string(record.get("Type of Work")),
                        "billed_value": DataNormalizer.normalize_numeric(
                            record.get("Billed Value in Rupees (Excl of GST.) (Masked)")
                            or record.get("Amount in Rupees (Excl of GST) (Masked)")
                        ),
                        "collected_amount": DataNormalizer.normalize_numeric(record.get("Collected Amount in Rupees (Incl of GST.) (Masked)")),
                        "invoice_status": DataNormalizer.normalize_string(record.get("Invoice Status")),
                        "billing_status": DataNormalizer.normalize_string(record.get("Billing Status")),
                    }
                )

            if any(r.get("sector") is None for r in normalized):
                missing_count = sum(1 for r in normalized if r.get("sector") is None)
                issues.append(f"{missing_count} work orders have missing or unrecognized sector values.")
            if any(r.get("billed_value") is None for r in normalized):
                missing_count = sum(1 for r in normalized if r.get("billed_value") is None)
                issues.append(f"{missing_count} work orders are missing billed values.")

            self.work_orders_cache = normalized
            self.data_quality_issues = issues
            return normalized, issues
        except MondayAPIError as exc:
            logger.error("Work orders fetch failed: %s", exc)
            return [], [f"I couldn't retrieve the Work Orders board from Monday.com right now: {exc}"]

    def plan_query(self, question: str) -> Dict[str, Any]:
        question_lower = question.lower()
        boards_needed: List[str] = []

        if any(keyword in question_lower for keyword in prompts.PIPELINE_KEYWORDS + prompts.SECTOR_COMPARISON_KEYWORDS):
            boards_needed.append("Deals")
        if any(keyword in question_lower for keyword in prompts.WORK_ORDER_KEYWORDS + prompts.REVENUE_KEYWORDS):
            boards_needed.append("WorkOrders")
        if not boards_needed:
            boards_needed = ["Deals", "WorkOrders"]

        metrics = self._infer_metrics(question)
        if "leadership" in question_lower or "executive" in question_lower or "summary" in question_lower:
            metrics.append("leadership")

        return {
            "original_question": question,
            "boards_needed": boards_needed,
            "needs_clarification": False,
            "clarification_question": None,
            "metrics": metrics,
        }

    def _infer_metrics(self, question: str) -> List[str]:
        q = question.lower()
        metrics: List[str] = []
        if any(token in q for token in ["total", "sum", "value", "how much", "pipeline"]):
            metrics.append("total_value")
        if any(token in q for token in ["sector", "by sector", "compare", "vs", "versus", "strongest"]):
            metrics.append("by_sector")
        if any(token in q for token in ["stage", "by stage"]):
            metrics.append("by_stage")
        if any(token in q for token in ["count", "many", "number", "how many"]):
            metrics.append("counts")
        if any(token in q for token in ["active", "open", "in progress"]):
            metrics.append("active")
        if any(token in q for token in ["delayed", "overdue", "late", "at risk"]):
            metrics.append("delayed")
        if any(token in q for token in ["average", "avg", "typical"]):
            metrics.append("averages")
        if any(token in q for token in ["revenue", "billed", "invoiced", "earnings"]):
            metrics.append("revenue")
        return metrics or ["overview"]

    def execute_query(self, question: str) -> Dict[str, Any]:
        logger.info("Processing question: %s", question)
        plan = self.plan_query(question)

        if plan.get("needs_clarification"):
            return {"success": True, "type": "clarification", "message": plan.get("clarification_question")}

        try:
            results: Dict[str, Any] = {}
            if "Deals" in plan.get("boards_needed", []):
                deals, deal_issues = self.fetch_and_normalize_deals()
                results["deals"] = deals
                results["deal_issues"] = deal_issues
            if "WorkOrders" in plan.get("boards_needed", []):
                work_orders, work_order_issues = self.fetch_and_normalize_work_orders()
                results["work_orders"] = work_orders
                results["work_order_issues"] = work_order_issues

            analysis = self._analyze(question, results, plan.get("metrics", []))
            response = self._format_response(question, analysis)
            caveats = results.get("deal_issues", []) + results.get("work_order_issues", [])
            return {"success": True, "type": "analysis", "response": response, "analysis": analysis, "caveats": caveats}
        except Exception as exc:  # pragma: no cover - safety net
            logger.exception("Query execution failed")
            return {"success": False, "type": "error", "message": f"I couldn't process that question right now: {exc}"}

    def _analyze(self, question: str, results: Dict[str, Any], metrics: List[str]) -> Dict[str, Any]:
        analysis: Dict[str, Any] = {}
        deals = results.get("deals", [])
        work_orders = results.get("work_orders", [])

        if deals:
            total_pipeline, total_count = Analytics.calculate_total_pipeline(deals)
            analysis["pipeline_total"] = {"value": total_pipeline, "count": total_count}

            active_pipeline, active_count = Analytics.calculate_active_pipeline(deals)
            analysis["active_pipeline"] = {"value": active_pipeline, "count": active_count}

            analysis["pipeline_by_sector"] = Analytics.pipeline_by_sector(deals)
            analysis["pipeline_by_stage"] = Analytics.pipeline_by_stage(deals)
            analysis["average_deal_size"] = Analytics.calculate_average_deal_size(deals)

        if work_orders:
            billed_total, billed_count = Analytics.calculate_billed_value(work_orders)
            analysis["billed_value"] = {"value": billed_total, "count": billed_count}
            delayed = Analytics.detect_delayed_work_orders(work_orders)
            analysis["work_orders_status"] = {
                "active": Analytics.count_active_work_orders(work_orders),
                "completed": Analytics.count_completed_work_orders(work_orders),
                "delayed": len(delayed),
            }
            analysis["work_orders_by_sector"] = Analytics.work_orders_by_sector(work_orders)

        return analysis

    def _format_response(self, question: str, analysis: Dict[str, Any]) -> str:
        q = question.lower()
        lines: List[str] = []

        if any(token in q for token in ["pipeline", "how's our pipeline", "total pipeline"]):
            if "pipeline_total" in analysis:
                total = analysis["pipeline_total"]["value"]
                count = analysis["pipeline_total"]["count"]
                lines.append(f"Total pipeline is ${total:,.0f} across {count} deals.")
            if "active_pipeline" in analysis:
                active = analysis["active_pipeline"]["value"]
                active_count = analysis["active_pipeline"]["count"]
                lines.append(f"Active pipeline is ${active:,.0f} across {active_count} active deals.")

        if any(token in q for token in ["sector", "compare", "vs", "versus", "strongest"]):
            if "pipeline_by_sector" in analysis:
                lines.append("Pipeline by sector:")
                for sector, (value, count) in sorted(analysis["pipeline_by_sector"].items(), key=lambda item: item[1][0], reverse=True):
                    lines.append(f"- {sector}: ${value:,.0f} ({count} deals)")

        if any(token in q for token in ["revenue", "billed", "invoiced", "how much", "earnings"]):
            if "billed_value" in analysis:
                total = analysis["billed_value"]["value"]
                lines.append(f"Total billed value is ${total:,.0f}.")

        if any(token in q for token in ["work order", "delayed", "project", "execution", "completed"]):
            if "work_orders_status" in analysis:
                status = analysis["work_orders_status"]
                lines.append(f"Work orders: {status['active']} active, {status['completed']} completed, {status['delayed']} delayed.")

        if not lines:
            lines.append("I analyzed the available data and here is the current picture.")
            if "pipeline_total" in analysis:
                total = analysis["pipeline_total"]["value"]
                lines.append(f"Pipeline value: ${total:,.0f}")
            if "work_orders_status" in analysis:
                status = analysis["work_orders_status"]
                lines.append(f"Open work orders: {status['active']} | completed: {status['completed']} | delayed: {status['delayed']}")

        return "\n".join(lines)

    def generate_leadership_summary(self) -> Dict[str, Any]:
        deals, deal_issues = self.fetch_and_normalize_deals()
        work_orders, work_order_issues = self.fetch_and_normalize_work_orders()
        summary = Analytics.generate_leadership_summary(deals, work_orders, deal_issues + work_order_issues)
        return {"success": True, "summary": summary, "timestamp": datetime.now().isoformat()}
