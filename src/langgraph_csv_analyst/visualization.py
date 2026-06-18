"""Visualization module using Plotly for CSV analysis charts."""

from __future__ import annotations

from typing import Any

import markdown as md_lib
import plotly.graph_objects as go


def create_profile_charts(profile: dict[str, Any]) -> list[go.Figure]:
    """Create profile visualization charts.

    Args:
        profile: The data profile dictionary.

    Returns:
        A list of Plotly figures.
    """
    charts: list[go.Figure] = []

    columns = profile.get("columns", [])
    if not columns:
        return charts

    # Null percentage bar chart
    null_data = [(col["name"], col["null_pct"]) for col in columns if col["null_pct"] > 0]
    if null_data:
        fig_null = go.Figure()
        fig_null.add_trace(
            go.Bar(
                x=[d[0] for d in null_data],
                y=[d[1] for d in null_data],
                marker_color="#ef4444",
            )
        )
        fig_null.update_layout(
            title="Null Percentage by Column",
            xaxis_title="Column",
            yaxis_title="Null %",
            template="plotly_white",
        )
        charts.append(fig_null)

    # Numeric columns distribution
    numeric_cols = [col for col in columns if "mean" in col.get("stats", {})]
    if numeric_cols:
        fig_stats = go.Figure()
        fig_stats.add_trace(
            go.Bar(
                x=[col["name"] for col in numeric_cols],
                y=[col["stats"].get("mean", 0) or 0 for col in numeric_cols],
                name="Mean",
                marker_color="#3b82f6",
            )
        )
        fig_stats.add_trace(
            go.Bar(
                x=[col["name"] for col in numeric_cols],
                y=[col["stats"].get("std", 0) or 0 for col in numeric_cols],
                name="Std Dev",
                marker_color="#f59e0b",
            )
        )
        fig_stats.update_layout(
            title="Numeric Column Statistics",
            xaxis_title="Column",
            yaxis_title="Value",
            barmode="group",
            template="plotly_white",
        )
        charts.append(fig_stats)

    # Unique value counts
    fig_unique = go.Figure()
    fig_unique.add_trace(
        go.Bar(
            x=[col["name"] for col in columns],
            y=[col["unique_count"] for col in columns],
            marker_color="#8b5cf6",
        )
    )
    fig_unique.update_layout(
        title="Unique Values by Column",
        xaxis_title="Column",
        yaxis_title="Unique Count",
        template="plotly_white",
    )
    charts.append(fig_unique)

    return charts


def create_trend_charts(trends: dict[str, Any]) -> list[go.Figure]:
    """Create trend visualization charts.

    Args:
        trends: The trend analysis dictionary.

    Returns:
        A list of Plotly figures.
    """
    charts: list[go.Figure] = []

    numeric_columns = trends.get("numeric_columns", [])
    categorical_columns = trends.get("categorical_columns", [])

    # Column type distribution pie chart
    if numeric_columns or categorical_columns:
        fig_types = go.Figure()
        fig_types.add_trace(
            go.Pie(
                labels=["Numeric Columns", "Categorical Columns"],
                values=[len(numeric_columns), len(categorical_columns)],
                marker_colors=["#3b82f6", "#10b981"],
            )
        )
        fig_types.update_layout(
            title="Column Type Distribution",
            template="plotly_white",
        )
        charts.append(fig_types)

    return charts


def create_anomaly_charts(anomalies: dict[str, Any]) -> list[go.Figure]:
    """Create anomaly visualization charts.

    Args:
        anomalies: The anomaly detection dictionary.

    Returns:
        A list of Plotly figures.
    """
    charts: list[go.Figure] = []

    anomaly_columns = anomalies.get("columns", {})
    if not anomaly_columns:
        return charts

    # Outlier count by column
    fig_outliers = go.Figure()
    fig_outliers.add_trace(
        go.Bar(
            x=list(anomaly_columns.keys()),
            y=[info["outlier_count"] for info in anomaly_columns.values()],
            marker_color="#ef4444",
        )
    )
    fig_outliers.update_layout(
        title="Outlier Count by Column",
        xaxis_title="Column",
        yaxis_title="Outlier Count",
        template="plotly_white",
    )
    charts.append(fig_outliers)

    # Outlier percentage by column
    fig_pct = go.Figure()
    fig_pct.add_trace(
        go.Bar(
            x=list(anomaly_columns.keys()),
            y=[info["outlier_pct"] for info in anomaly_columns.values()],
            marker_color="#f59e0b",
        )
    )
    fig_pct.update_layout(
        title="Outlier Percentage by Column",
        xaxis_title="Column",
        yaxis_title="Outlier %",
        template="plotly_white",
    )
    charts.append(fig_pct)

    return charts


def create_investment_charts(investment_analysis: dict[str, Any]) -> list[go.Figure]:
    """Create investment analysis visualization charts.

    Args:
        investment_analysis: The investment analysis dictionary from asset-lens CSV.

    Returns:
        A list of Plotly figures.
    """
    charts: list[go.Figure] = []

    if not investment_analysis or investment_analysis.get("source") != "asset-lens":
        return charts

    # Return distribution pie chart
    distribution = investment_analysis.get("return_distribution", {})
    if distribution:
        colors = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6", "#ec4899"]
        fig_dist = go.Figure()
        fig_dist.add_trace(
            go.Pie(
                labels=list(distribution.keys()),
                values=list(distribution.values()),
                marker_colors=colors[: len(distribution)],
                textinfo="label+percent+value",
            )
        )
        fig_dist.update_layout(
            title="Investment Return Distribution",
            template="plotly_white",
        )
        charts.append(fig_dist)

    # Return stats bar chart
    return_stats = investment_analysis.get("return_stats", {})
    if return_stats:
        fig_stats = go.Figure()
        fig_stats.add_trace(
            go.Bar(
                x=["Mean", "Median", "Min", "Max", "Std Dev"],
                y=[
                    return_stats.get("mean", 0),
                    return_stats.get("median", 0),
                    return_stats.get("min", 0),
                    return_stats.get("max", 0),
                    return_stats.get("std", 0),
                ],
                marker_color=["#3b82f6", "#10b981", "#ef4444", "#8b5cf6", "#f59e0b"],
            )
        )
        fig_stats.update_layout(
            title="Return Rate Statistics (%)",
            xaxis_title="Metric",
            yaxis_title="Return %",
            template="plotly_white",
        )
        charts.append(fig_stats)

    # Risk assessment chart
    risk = investment_analysis.get("risk_assessment", {})
    if risk:
        fig_risk = go.Figure()
        fig_risk.add_trace(
            go.Bar(
                x=["Positive Return", "Low Return (<2%)", "Negative Return"],
                y=[
                    (investment_analysis.get("total_products", 0) - risk.get("low_return_count", 0)),
                    risk.get("low_return_count", 0) - risk.get("negative_return_count", 0),
                    risk.get("negative_return_count", 0),
                ],
                marker_color=["#10b981", "#f59e0b", "#ef4444"],
            )
        )
        fig_risk.update_layout(
            title="Portfolio Risk Assessment",
            xaxis_title="Category",
            yaxis_title="Product Count",
            template="plotly_white",
        )
        charts.append(fig_risk)

    return charts


def generate_html_report(all_charts: list[go.Figure], metadata: dict[str, Any]) -> str:
    """Generate a self-contained HTML report from all charts.

    Args:
        all_charts: List of Plotly figures to include.
        metadata: Report metadata (csv_path, stats, LLM analysis, etc.).

    Returns:
        A complete HTML string.
    """
    chart_html_parts = []
    for i, fig in enumerate(all_charts):
        chart_html_parts.append(
            f'<div class="chart-container">\n'
            f"  {fig.to_html(full_html=False, include_plotlyjs=False)}\n"
            f"</div>"
        )

    charts_html = "\n".join(chart_html_parts)

    # Build LLM analysis sections
    analysis_sections = ""

    trend_analysis = metadata.get("trend_analysis", "")
    if trend_analysis:
        analysis_sections += f"""
        <div class="analysis-card">
            <h2>📊 趋势分析</h2>
            <div class="analysis-content">{_format_markdown_text(trend_analysis)}</div>
        </div>"""

    anomaly_analysis = metadata.get("anomaly_analysis", "")
    if anomaly_analysis:
        analysis_sections += f"""
        <div class="analysis-card">
            <h2>🔍 异常解读</h2>
            <div class="analysis-content">{_format_markdown_text(anomaly_analysis)}</div>
        </div>"""

    investment_insights = metadata.get("investment_insights", "")
    investment_stats = metadata.get("investment_stats", {})

    if investment_insights or investment_stats:
        # Investment stats cards
        stats_cards = ""
        return_stats = investment_stats.get("return_stats", {})
        if return_stats:
            stats_cards += f"""
            <div class="stats-grid">
                <div class="stat-card stat-blue">
                    <div class="stat-value">{return_stats.get('mean', 0)}%</div>
                    <div class="stat-label">平均收益率</div>
                </div>
                <div class="stat-card stat-green">
                    <div class="stat-value">{return_stats.get('median', 0)}%</div>
                    <div class="stat-label">中位数收益率</div>
                </div>
                <div class="stat-card stat-purple">
                    <div class="stat-value">{return_stats.get('max', 0)}%</div>
                    <div class="stat-label">最高收益率</div>
                </div>
                <div class="stat-card stat-red">
                    <div class="stat-value">{return_stats.get('min', 0)}%</div>
                    <div class="stat-label">最低收益率</div>
                </div>
            </div>"""

        amount_stats = investment_stats.get("amount_stats", {})
        if amount_stats:
            stats_cards += f"""
            <div class="stats-grid">
                <div class="stat-card stat-blue">
                    <div class="stat-value">¥{amount_stats.get('total', 0):,.0f}</div>
                    <div class="stat-label">持仓总额</div>
                </div>
                <div class="stat-card stat-green">
                    <div class="stat-value">¥{amount_stats.get('mean', 0):,.0f}</div>
                    <div class="stat-label">平均持仓</div>
                </div>
            </div>"""

        risk_assessment = investment_stats.get("risk_assessment", {})
        if risk_assessment:
            risk_warnings = ""
            negative_products = risk_assessment.get("negative_return_products", [])
            low_return_products = risk_assessment.get("low_return_products", [])
            if negative_products:
                risk_warnings += f"""
                <div class="risk-item risk-negative">
                    <strong>亏损产品 ({len(negative_products)}个):</strong> {', '.join(str(p) for p in negative_products)}
                </div>"""
            if low_return_products:
                risk_warnings += f"""
                <div class="risk-item risk-low">
                    <strong>低收益产品 ({risk_assessment.get('low_return_count', 0)}个):</strong> 收益率低于2%
                </div>"""
            if risk_warnings:
                stats_cards += f"""
            <div class="risk-section">
                <h3>⚠️ 风险提示</h3>
                {risk_warnings}
            </div>"""

        insights_html = ""
        if investment_insights:
            insights_html = f"""
            <div class="analysis-content">{_format_markdown_text(investment_insights)}</div>"""

        analysis_sections += f"""
        <div class="analysis-card">
            <h2>💰 投资洞察</h2>
            {stats_cards}
            {insights_html}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV 分析报告 - {metadata.get('csv_path', 'Unknown')}</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{ font-size: 1.8rem; margin-bottom: 0.5rem; }}
        .header p {{ opacity: 0.9; }}
        .metadata {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            padding: 1.5rem;
            background: white;
            border-bottom: 1px solid #e2e8f0;
        }}
        .metadata-item {{
            text-align: center;
        }}
        .metadata-item .value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #3b82f6;
        }}
        .metadata-item .label {{
            font-size: 0.85rem;
            color: #64748b;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .analysis-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .analysis-card h2 {{
            font-size: 1.2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e2e8f0;
            color: #1e293b;
        }}
        .analysis-content {{
            color: #475569;
            line-height: 1.8;
        }}
        .analysis-content h1 {{ font-size: 1.2rem; margin: 1rem 0 0.5rem; color: #1e293b; }}
        .analysis-content h2 {{ font-size: 1.1rem; margin: 1rem 0 0.5rem; color: #1e293b; }}
        .analysis-content h3 {{ font-size: 1rem; margin: 0.8rem 0 0.4rem; color: #334155; }}
        .analysis-content p {{ margin: 0.5rem 0; }}
        .analysis-content ul, .analysis-content ol {{ margin: 0.5rem 0; padding-left: 1.5rem; }}
        .analysis-content li {{ margin: 0.3rem 0; }}
        .analysis-content strong {{ color: #1e293b; }}
        .analysis-content em {{ color: #64748b; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        .stat-card {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            border-left: 4px solid;
        }}
        .stat-blue {{ border-color: #3b82f6; }}
        .stat-green {{ border-color: #10b981; }}
        .stat-purple {{ border-color: #8b5cf6; }}
        .stat-red {{ border-color: #ef4444; }}
        .stat-value {{
            font-size: 1.4rem;
            font-weight: 700;
            color: #1e293b;
        }}
        .stat-label {{
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 0.25rem;
        }}
        .risk-section {{
            background: #fffbeb;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid #fde68a;
        }}
        .risk-section h3 {{
            font-size: 1rem;
            margin-bottom: 0.75rem;
            color: #92400e;
        }}
        .risk-item {{
            padding: 0.5rem 0.75rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
            font-size: 0.9rem;
        }}
        .risk-negative {{
            background: #fef2f2;
            color: #991b1b;
            border-left: 3px solid #ef4444;
        }}
        .risk-low {{
            background: #fffbeb;
            color: #92400e;
            border-left: 3px solid #f59e0b;
        }}
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #94a3b8;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>CSV 分析报告</h1>
        <p>{metadata.get('csv_path', 'Unknown')}</p>
    </div>
    <div class="metadata">
        <div class="metadata-item">
            <div class="value">{metadata.get('total_rows', 0):,}</div>
            <div class="label">数据行数</div>
        </div>
        <div class="metadata-item">
            <div class="value">{metadata.get('total_columns', 0)}</div>
            <div class="label">字段数</div>
        </div>
        <div class="metadata-item">
            <div class="value">{metadata.get('total_anomalies', 0)}</div>
            <div class="label">异常值</div>
        </div>
    </div>
    <div class="container">
        {analysis_sections}
        {charts_html}
    </div>
    <div class="footer">
        Generated by LangGraph CSV Analyst
    </div>
</body>
</html>"""

    return html


def _format_markdown_text(text: str) -> str:
    """Convert Markdown text to HTML using the markdown library."""
    if not text:
        return ""
    return md_lib.markdown(text, extensions=["extra", "nl2br"])
