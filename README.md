# LangGraph CSV Analyst

[中文文档](README.zh-CN.md)

A CSV analysis tool using LangGraph multi-agent pipeline for automated data profiling, trend analysis, anomaly detection, and **investment portfolio analysis** (asset-lens integration) with HTML report generation.

## Architecture

```
                    ┌─────────────┐
                    │   CSV File   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Parser    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┬────────────┐
              │            │            │            │
     ┌────────▼───┐ ┌──────▼─────┐ ┌───▼────────┐ ┌──▼──────────┐
     │  Profiler   │ │   Trend    │ │  Anomaly   │ │ Investment  │
     │   Agent     │ │ Analyzer   │ │  Detector  │ │  Analyzer   │
     └────────┬───┘ └──────┬─────┘ └───┬────────┘ └──┬──────────┘
              │            │            │              │
              └────────────┼────────────┼──────────────┘
                           │            │
                  ┌────────▼────────────▼┐
                  │     Report           │
                  │    Generator         │
                  └────────┬─────────────┘
                           │
                  ┌────────▼────────┐
                  │   HTML Report   │
                  └─────────────────┘
```

### Investment Analyzer (asset-lens)

When the input CSV is an asset-lens output (`投资收益率分析_*.csv`), the Investment Analyzer automatically:

- **Detects** asset-lens format by column keywords (return rate, IRR, annualized, etc.)
- **Calculates** return distribution (loss / 0-2% / 2-5% / 5-10% / 10-20% / 20%+)
- **Assesses** portfolio risk (low return, negative return products)
- **Generates** LLM-powered insights (health assessment, rebalancing suggestions)
- **Visualizes** return distribution pie chart, return stats bar chart, risk assessment chart

## Project Structure

```
langgraph-csv-analyst/
├── src/langgraph_csv_analyst/
│   ├── __init__.py          # Package init with version
│   ├── config.py            # Configuration (pydantic-settings)
│   ├── csv_parser.py        # CSV parsing and profiling
│   ├── agents.py            # Multi-agent definitions
│   ├── graph.py             # LangGraph state graph
│   ├── visualization.py     # Plotly chart generation + HTML report
│   ├── api.py               # FastAPI service
│   └── cli.py               # CLI (Typer)
├── tests/
│   ├── __init__.py
│   └── test_csv_parser.py   # CSV parser tests
├── pyproject.toml
├── .env.example
├── .gitignore
├── Makefile
├── README.md
└── README.zh-CN.md
```

## Quick Start

### 1. Install Dependencies

```bash
cd invest-kit/apps/langgraph-csv-analyst
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### 3. Run Analysis

```bash
# Full analysis with HTML report
uv run langgraph-analyst analyze sample.csv

# Quick data profile
uv run langgraph-analyst profile sample.csv

# Start API server
uv run langgraph-analyst-api
```

Or use Make:

```bash
make install
make analyze FILE=sample.csv
make profile FILE=sample.csv
make api
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Upload CSV and run full analysis |
| `GET` | `/api/v1/report/{task_id}` | Get analysis report |
| `GET` | `/api/v1/health` | Health check |

### Example: Upload and Analyze

```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -F "file=@sample.csv"
```

### Example: Get Report

```bash
curl "http://localhost:8001/api/v1/report/{task_id}"
```

## Configuration

All settings are loaded from `.env` file using pydantic-settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `deepseek-chat` | LLM model name |
| `OPENAI_API_KEY` | - | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | API base URL |
| `CSV_MAX_SIZE_MB` | `50` | Maximum CSV file size in MB |
| `MAX_ROWS_DISPLAY` | `100` | Maximum rows to display |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8001` | API server port |
| `DEBUG` | `False` | Debug mode |

## LangGraph State Graph

The analysis pipeline is built as a LangGraph `StateGraph` with the following flow:

1. **load_csv** - Load and validate the CSV file
2. **profile** - Profile data types, statistics, and null counts
3. **Parallel Execution**:
   - **trend_analyzer** - Analyze trends and patterns using LLM
   - **anomaly_detector** - Detect outliers using IQR method + LLM analysis
   - **investment_analyzer** - Analyze investment portfolio (asset-lens format)
4. **generate_report** - Compile all results into an HTML report

The `AnalysisState` TypedDict tracks:

```python
class AnalysisState(TypedDict, total=False):
    csv_path: str              # Input CSV file path
    dataframe_info: dict       # Shape, columns, dtypes
    profile: dict              # Full data profile
    trends: dict               # Trend analysis results
    anomalies: dict            # Anomaly detection results
    report: str                # Generated HTML report
    errors: list[str]          # Collected errors
```

Error handling is integrated via conditional edges that route to an `error_handler` node when errors are detected at any stage.

## License

MIT
