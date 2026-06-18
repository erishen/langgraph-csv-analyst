"""Multi-agent definitions using LangGraph for CSV analysis."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from langgraph_csv_analyst.config import settings
from langgraph_csv_analyst.csv_parser import detect_anomalies, get_profile, load_csv


def _get_llm() -> BaseChatModel:
    """Get the configured LLM instance."""
    return ChatOpenAI(
        model=settings.DEFAULT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        temperature=settings.DEFAULT_TEMPERATURE,
    )


def data_profiler_agent(state: dict[str, Any]) -> dict[str, Any]:
    """Profile CSV data: types, stats, nulls.

    Args:
        state: The current analysis state containing csv_path.

    Returns:
        Updated state with profile and dataframe_info.
    """
    try:
        csv_path = state.get("csv_path")
        if not csv_path:
            return {"errors": ["No CSV path provided"]}

        df = load_csv(csv_path)
        profile = get_profile(df)

        return {
            "dataframe_info": {
                "shape": {"rows": len(df), "columns": len(df.columns)},
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            },
            "profile": profile,
        }
    except Exception as e:
        return {"errors": [f"DataProfilerAgent error: {str(e)}"]}


def trend_analyzer_agent(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze trends and patterns in the data.

    Uses LLM to provide natural language trend analysis based on the profile.

    Args:
        state: The current analysis state with profile data.

    Returns:
        Updated state with trends analysis.
    """
    try:
        profile = state.get("profile")
        if not profile:
            return {"errors": ["No profile data available for trend analysis"]}

        columns_summary = []
        for col in profile.get("columns", []):
            col_desc = f"- {col['name']} ({col['dtype']}): {col['null_count']} nulls, {col['unique_count']} unique values"
            if "stats" in col and "mean" in col["stats"]:
                col_desc += f", mean={col['stats']['mean']}, std={col['stats']['std']}"
            columns_summary.append(col_desc)

        columns_text = "\n".join(columns_summary)

        prompt = (
            f"分析以下 CSV 数据概况，识别关键趋势和模式。\n\n"
            f"总行数: {profile.get('total_rows', 0)}\n"
            f"总列数: {profile.get('total_columns', 0)}\n\n"
            f"列详情:\n{columns_text}\n\n"
            f"请提供简洁的趋势分析，涵盖:\n"
            f"1. 数据分布模式\n"
            f"2. 数值列之间的相关性（如有）\n"
            f"3. 分类数据中的显著模式\n"
            f"4. 数据质量观察"
        )

        llm = _get_llm()
        response = llm.invoke(prompt)
        trends = {
            "analysis": response.content,
            "numeric_columns": [
                col["name"]
                for col in profile.get("columns", [])
                if "mean" in col.get("stats", {})
            ],
            "categorical_columns": [
                col["name"]
                for col in profile.get("columns", [])
                if "top_values" in col.get("stats", {})
            ],
        }

        return {"trends": trends}
    except Exception as e:
        return {"errors": [f"TrendAnalyzerAgent error: {str(e)}"]}


def anomaly_detector_agent(state: dict[str, Any]) -> dict[str, Any]:
    """Detect outliers and anomalies in the data.

    Uses IQR method for statistical outlier detection and LLM for contextual analysis.

    Args:
        state: The current analysis state with csv_path.

    Returns:
        Updated state with anomaly detection results.
    """
    try:
        csv_path = state.get("csv_path")
        if not csv_path:
            return {"errors": ["No CSV path provided for anomaly detection"]}

        df = load_csv(csv_path)
        anomalies = detect_anomalies(df)

        anomaly_summary = []
        for col_name, col_info in anomalies.get("columns", {}).items():
            anomaly_summary.append(
                f"- {col_name}: {col_info['outlier_count']} outliers "
                f"({col_info['outlier_pct']}%), "
                f"bounds=[{col_info['lower_bound']}, {col_info['upper_bound']}]"
            )

        if anomaly_summary:
            anomaly_text = "\n".join(anomaly_summary)
            prompt = (
                f"分析以下异常检测结果并提供见解。\n\n"
                f"发现异常总数: {anomalies.get('total_anomalies', 0)}\n\n"
                f"异常详情:\n{anomaly_text}\n\n"
                f"请提供:\n"
                f"1. 异常严重程度评估\n"
                f"2. 各异常的可能原因\n"
                f"3. 处理建议"
            )
            llm = _get_llm()
            response = llm.invoke(prompt)
            anomalies["llm_analysis"] = response.content

        return {"anomalies": anomalies}
    except Exception as e:
        return {"errors": [f"AnomalyDetectorAgent error: {str(e)}"]}


def report_generator_agent(state: dict[str, Any]) -> dict[str, Any]:
    """Generate the final visualization report.

    Args:
        state: The current analysis state with all analysis results.

    Returns:
        Updated state with the generated report.
    """
    try:
        from langgraph_csv_analyst.visualization import (
            generate_html_report,
            create_anomaly_charts,
            create_investment_charts,
            create_profile_charts,
            create_trend_charts,
        )

        profile = state.get("profile", {})
        trends = state.get("trends", {})
        anomalies = state.get("anomalies", {})
        investment_analysis = state.get("investment_analysis", {})

        all_charts = []
        all_charts.extend(create_profile_charts(profile))
        all_charts.extend(create_trend_charts(trends))
        all_charts.extend(create_anomaly_charts(anomalies))
        all_charts.extend(create_investment_charts(investment_analysis))

        metadata = {
            "csv_path": state.get("csv_path", "unknown"),
            "total_rows": profile.get("total_rows", 0),
            "total_columns": profile.get("total_columns", 0),
            "total_anomalies": anomalies.get("total_anomalies", 0),
            "trend_analysis": trends.get("analysis", ""),
            "anomaly_analysis": anomalies.get("llm_analysis", ""),
            "investment_insights": investment_analysis.get("llm_insights", ""),
            "investment_stats": {
                "return_stats": investment_analysis.get("return_stats", {}),
                "return_distribution": investment_analysis.get("return_distribution", {}),
                "risk_assessment": investment_analysis.get("risk_assessment", {}),
                "amount_stats": investment_analysis.get("amount_stats", {}),
            } if investment_analysis.get("source") == "asset-lens" else {},
        }

        html_report = generate_html_report(all_charts, metadata)

        return {"report": html_report}
    except Exception as e:
        return {"errors": [f"ReportGeneratorAgent error: {str(e)}"]}


def investment_analyzer_agent(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze investment return CSV from asset-lens.

    Detects asset-lens output format (columns like 产品名称, IRR年化收益率, etc.)
    and provides investment-specific analysis: portfolio overview, return distribution,
    risk assessment, and rebalancing suggestions.

    Args:
        state: The current analysis state with csv_path and profile.

    Returns:
        Updated state with investment analysis results.
    """
    try:
        csv_path = state.get("csv_path")
        profile = state.get("profile", {})
        if not csv_path:
            return {"errors": ["No CSV path provided for investment analysis"]}

        df = load_csv(csv_path)
        columns = list(df.columns)

        # Detect asset-lens format
        asset_lens_keywords = ["收益率", "年化", "IRR", "投资", "产品", "金额", "收益"]
        is_asset_lens = any(any(kw in col for kw in asset_lens_keywords) for col in columns)

        if not is_asset_lens:
            return {"investment_analysis": None}

        # Extract investment-specific metrics
        analysis: dict[str, Any] = {
            "source": "asset-lens",
            "total_products": len(df),
        }

        # Find return rate column
        return_col = next((c for c in columns if "年化收益率" in c or "IRR" in c), None)
        if return_col and df[return_col].dtype in ["float64", "int64", "float32"]:
            returns = df[return_col].dropna()
            analysis["return_stats"] = {
                "mean": round(float(returns.mean()), 2),
                "median": round(float(returns.median()), 2),
                "std": round(float(returns.std()), 2),
                "min": round(float(returns.min()), 2),
                "max": round(float(returns.max()), 2),
                "positive_count": int((returns > 0).sum()),
                "negative_count": int((returns < 0).sum()),
                "zero_count": int((returns == 0).sum()),
            }

            # Return distribution buckets
            bins = [-float("inf"), 0, 2, 5, 10, 20, float("inf")]
            labels = ["亏损", "0-2%", "2-5%", "5-10%", "10-20%", "20%+"]
            distribution = {}
            for i in range(len(labels)):
                if i == 0:
                    count = int((returns < 0).sum())
                elif i == len(labels) - 1:
                    count = int((returns >= bins[i]).sum())
                else:
                    count = int(((returns >= bins[i]) & (returns < bins[i + 1])).sum())
                distribution[labels[i]] = count
            analysis["return_distribution"] = distribution

            # Risk assessment
            low_return_threshold = 2.0  # Below bank deposit rate
            low_return_products = df[df[return_col] < low_return_threshold]
            negative_products = df[df[return_col] < 0]

            name_col = next((c for c in columns if "名称" in c or "产品" in c), None)
            analysis["risk_assessment"] = {
                "low_return_count": len(low_return_products),
                "negative_return_count": len(negative_products),
                "low_return_products": (
                    low_return_products[name_col].tolist()[:10] if name_col else []
                ),
                "negative_return_products": (
                    negative_products[name_col].tolist()[:10] if name_col else []
                ),
            }

        # Find amount column
        amount_col = next((c for c in columns if "当前金额" in c or "金额" in c), None)
        if amount_col and df[amount_col].dtype in ["float64", "int64", "float32"]:
            amounts = df[amount_col].dropna()
            analysis["amount_stats"] = {
                "total": round(float(amounts.sum()), 2),
                "mean": round(float(amounts.mean()), 2),
                "max": round(float(amounts.max()), 2),
                "min": round(float(amounts.min()), 2),
            }

        # LLM analysis for investment insights
        if analysis.get("return_stats"):
            prompt = (
                f"分析以下投资组合数据并提供见解。\n\n"
                f"组合产品数: {analysis['total_products']}个\n"
                f"收益率统计: 均值={analysis['return_stats']['mean']}%, "
                f"中位数={analysis['return_stats']['median']}%, "
                f"标准差={analysis['return_stats']['std']}%\n"
                f"收益分布: {analysis['return_distribution']}\n"
                f"风险: {analysis['risk_assessment']['low_return_count']}个低收益, "
                f"{analysis['risk_assessment']['negative_return_count']}个亏损\n\n"
                f"请提供:\n"
                f"1. 组合健康度评估\n"
                f"2. 收益分布分析\n"
                f"3. 风险警示\n"
                f"4. 再平衡建议"
            )
            llm = _get_llm()
            response = llm.invoke(prompt)
            analysis["llm_insights"] = response.content

        return {"investment_analysis": analysis}
    except Exception as e:
        return {"errors": [f"InvestmentAnalyzerAgent error: {str(e)}"]}


def error_handler_node(state: dict[str, Any]) -> dict[str, Any]:
    """Handle errors collected during the analysis pipeline.

    Args:
        state: The current analysis state with potential errors.

    Returns:
        Updated state with error summary.
    """
    errors = state.get("errors", [])
    if errors:
        return {"errors": errors}
    return {}
