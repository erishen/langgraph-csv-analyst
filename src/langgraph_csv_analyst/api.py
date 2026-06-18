"""FastAPI service for CSV analysis."""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from typing import Any

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langgraph_csv_analyst.config import settings
from langgraph_csv_analyst.csv_parser import get_profile, get_summary, load_csv
from langgraph_csv_analyst.graph import run_analysis

app = FastAPI(
    title=settings.APP_NAME,
    description="A CSV analysis tool using LangGraph multi-agent pipeline",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory task storage (use Redis/DB in production)
_task_store: dict[str, dict[str, Any]] = {}


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    app_name: str


class AnalysisResponse(BaseModel):
    """Analysis task response model."""

    task_id: str
    status: str
    message: str


class ReportResponse(BaseModel):
    """Report retrieval response model."""

    task_id: str
    status: str
    report: str | None = None
    profile: dict[str, Any] | None = None
    errors: list[str] | None = None


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        app_name=settings.APP_NAME,
    )


@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_csv(file: UploadFile = File(...)) -> AnalysisResponse:
    """Upload a CSV file and run the full analysis pipeline.

    Args:
        file: The uploaded CSV file.

    Returns:
        Analysis task information with task_id for retrieval.
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    task_id = str(uuid.uuid4())

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)

    try:
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        file_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if file_size_mb > settings.CSV_MAX_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"File size ({file_size_mb:.1f} MB) exceeds limit ({settings.CSV_MAX_SIZE_MB} MB)",
            )

        _task_store[task_id] = {
            "status": "processing",
            "csv_path": tmp_path,
        }

        result = run_analysis(tmp_path)

        _task_store[task_id] = {
            "status": "completed",
            "report": result.get("report", ""),
            "profile": result.get("profile", {}),
            "errors": result.get("errors", []),
        }

    except HTTPException:
        raise
    except Exception as e:
        _task_store[task_id] = {
            "status": "failed",
            "errors": [str(e)],
        }

    return AnalysisResponse(
        task_id=task_id,
        status=_task_store[task_id]["status"],
        message="Analysis completed" if _task_store[task_id]["status"] == "completed" else "Analysis failed",
    )


@app.get("/api/v1/report/{task_id}", response_model=ReportResponse)
async def get_report(task_id: str) -> ReportResponse:
    """Get the analysis report for a given task.

    Args:
        task_id: The task ID returned from the analyze endpoint.

    Returns:
        The analysis report and associated data.
    """
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Task not found")

    task = _task_store[task_id]

    return ReportResponse(
        task_id=task_id,
        status=task.get("status", "unknown"),
        report=task.get("report"),
        profile=task.get("profile"),
        errors=task.get("errors"),
    )


def run_server() -> None:
    """Run the FastAPI server."""
    uvicorn.run(
        "langgraph_csv_analyst.api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run_server()
