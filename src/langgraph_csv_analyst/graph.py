"""LangGraph state graph for CSV analysis pipeline."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from langgraph_csv_analyst.agents import (
    anomaly_detector_agent,
    data_profiler_agent,
    error_handler_node,
    investment_analyzer_agent,
    report_generator_agent,
    trend_analyzer_agent,
)
from langgraph_csv_analyst.csv_parser import load_csv


def _merge_lists(existing: list[str], new: list[str]) -> list[str]:
    """Merge two lists, appending new items to existing."""
    return existing + new


class AnalysisState(TypedDict, total=False):
    """State definition for the CSV analysis pipeline."""

    csv_path: str
    dataframe_info: dict[str, Any]
    profile: dict[str, Any]
    trends: dict[str, Any]
    anomalies: dict[str, Any]
    investment_analysis: dict[str, Any]
    report: str
    errors: Annotated[list[str], _merge_lists]


def load_csv_node(state: AnalysisState) -> dict[str, Any]:
    """Load CSV file and validate it.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with csv_path confirmed.
    """
    csv_path = state.get("csv_path", "")
    try:
        df = load_csv(csv_path)
        return {
            "dataframe_info": {
                "shape": {"rows": len(df), "columns": len(df.columns)},
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            },
        }
    except Exception as e:
        return {"errors": [f"Failed to load CSV: {str(e)}"]}


def profile_node(state: AnalysisState) -> dict[str, Any]:
    """Profile the CSV data.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with profile data.
    """
    return data_profiler_agent(state)


def trend_node(state: AnalysisState) -> dict[str, Any]:
    """Analyze trends in the data.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with trend analysis.
    """
    return trend_analyzer_agent(state)


def anomaly_node(state: AnalysisState) -> dict[str, Any]:
    """Detect anomalies in the data.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with anomaly detection results.
    """
    return anomaly_detector_agent(state)


def investment_node(state: AnalysisState) -> dict[str, Any]:
    """Analyze investment data if asset-lens format detected.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with investment analysis results.
    """
    return investment_analyzer_agent(state)


def report_node(state: AnalysisState) -> dict[str, Any]:
    """Generate the final report.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with the HTML report.
    """
    return report_generator_agent(state)


def error_node(state: AnalysisState) -> dict[str, Any]:
    """Handle errors in the pipeline.

    Args:
        state: The current analysis state.

    Returns:
        Updated state with error information.
    """
    return error_handler_node(state)


def should_continue_after_load(state: AnalysisState) -> str:
    """Decide whether to continue to profiling or handle errors."""
    errors = state.get("errors", [])
    if errors:
        return "error_handler"
    return "profile"


def should_continue_after_profile(state: AnalysisState) -> str:
    """Decide whether to continue to parallel analysis or handle errors."""
    errors = state.get("errors", [])
    if errors:
        return "error_handler"
    return "parallel_analysis"


def should_continue_after_report(state: AnalysisState) -> str:
    """Decide whether to end or handle errors."""
    errors = state.get("errors", [])
    if errors:
        return "error_handler"
    return END


def build_graph() -> StateGraph:
    """Build the LangGraph state graph for CSV analysis.

    Pipeline: load_csv -> profile -> [trend + anomaly parallel] -> generate_report

    Returns:
        A compiled StateGraph ready for execution.
    """
    graph = StateGraph(AnalysisState)

    # Add nodes
    graph.add_node("load_csv", load_csv_node)
    graph.add_node("profile", profile_node)
    graph.add_node("trend_analyzer", trend_node)
    graph.add_node("anomaly_detector", anomaly_node)
    graph.add_node("investment_analyzer", investment_node)
    graph.add_node("generate_report", report_node)
    graph.add_node("error_handler", error_node)

    # Set entry point
    graph.set_entry_point("load_csv")

    # Add conditional edges from load_csv
    graph.add_conditional_edges(
        "load_csv",
        should_continue_after_load,
        {
            "profile": "profile",
            "error_handler": "error_handler",
        },
    )

    # Add conditional edges from profile
    graph.add_conditional_edges(
        "profile",
        should_continue_after_profile,
        {
            "parallel_analysis": "trend_analyzer",
            "error_handler": "error_handler",
        },
    )

    # Profile also fans out to anomaly_detector and investment_analyzer
    graph.add_edge("profile", "anomaly_detector")
    graph.add_edge("profile", "investment_analyzer")

    # Parallel edges: trend_analyzer, anomaly_detector, investment_analyzer
    # all run after profile, then all go to generate_report
    graph.add_edge("trend_analyzer", "generate_report")
    graph.add_edge("anomaly_detector", "generate_report")
    graph.add_edge("investment_analyzer", "generate_report")

    # Note: In LangGraph, for true parallel execution, we need fan-out/fan-in.
    # The profile node fans out to both trend_analyzer and anomaly_detector.
    # Both converge at generate_report.

    # Error handler goes to END
    graph.add_edge("error_handler", END)

    # Conditional edges from generate_report
    graph.add_conditional_edges(
        "generate_report",
        should_continue_after_report,
        {
            END: END,
            "error_handler": "error_handler",
        },
    )

    return graph


def run_analysis(csv_path: str) -> AnalysisState:
    """Run the full CSV analysis pipeline.

    Args:
        csv_path: Path to the CSV file to analyze.

    Returns:
        The final analysis state with all results.
    """
    graph = build_graph()
    compiled = graph.compile()

    initial_state: AnalysisState = {
        "csv_path": csv_path,
        "dataframe_info": {},
        "profile": {},
        "trends": {},
        "anomalies": {},
        "investment_analysis": {},
        "report": "",
        "errors": [],
    }

    result = compiled.invoke(initial_state)
    return result
