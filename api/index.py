"""FastAPI entry point for the Vercel-hosted Skylark Drones BI API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent import Agent
from app.config import Config
from app.monday_client import MondayClient

logger = logging.getLogger(__name__)

app = FastAPI(title="Skylark Drones BI API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
agent = Agent()


class RefreshRequest(BaseModel):
    force_refresh: bool = False


class QuestionRequest(RefreshRequest):
    question: str = Field(min_length=3, max_length=1000)


def _require_monday_configuration() -> None:
    configured, missing = Config.validate()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail={"message": "Monday.com is not configured.", "missing": missing},
        )


def _has_retrieval_error(issues: list[str]) -> bool:
    return any(issue.startswith("I couldn't retrieve") for issue in issues)


@app.get("/api/health")
def health() -> dict[str, Any]:
    configured, missing = Config.validate()
    return {"status": "ok", "monday_configured": configured, "missing": missing}


@app.get("/api/connection")
def connection_status() -> dict[str, Any]:
    _require_monday_configuration()
    connected = MondayClient().test_connection()
    if not connected:
        raise HTTPException(status_code=502, detail="Unable to connect to Monday.com. Check the token and board access.")
    return {"connected": True}


@app.post("/api/dashboard")
def dashboard(request: RefreshRequest) -> dict[str, Any]:
    _require_monday_configuration()
    deals, deal_issues = agent.fetch_and_normalize_deals(force_refresh=request.force_refresh)
    work_orders, work_order_issues = agent.fetch_and_normalize_work_orders(force_refresh=request.force_refresh)
    issues = deal_issues + work_order_issues
    if _has_retrieval_error(issues):
        raise HTTPException(status_code=502, detail={"message": "Monday.com data retrieval failed.", "issues": issues})

    return {
        "summary": agent.generate_leadership_summary()["summary"],
        "deals_count": len(deals),
        "work_orders_count": len(work_orders),
        "data_quality_issues": issues,
    }


@app.post("/api/questions")
def ask_question(request: QuestionRequest) -> dict[str, Any]:
    _require_monday_configuration()
    if request.force_refresh:
        agent.fetch_and_normalize_deals(force_refresh=True)
        agent.fetch_and_normalize_work_orders(force_refresh=True)
    result = agent.execute_query(request.question.strip())
    if not result["success"]:
        logger.error("Question processing failed: %s", result.get("message"))
        raise HTTPException(status_code=502, detail=result.get("message", "Unable to process the question."))
    return result
