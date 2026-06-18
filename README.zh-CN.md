# LangGraph CSV 分析工具

[English](README.md)

基于 LangGraph 多智能体流水线的 CSV 分析工具，支持自动化数据画像、趋势分析、异常检测和**投资组合分析**（asset-lens 集成），并生成 HTML 可视化报告。

## 架构

```
                    ┌─────────────┐
                    │   CSV 文件   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    解析器    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┬────────────┐
              │            │            │            │
     ┌────────▼───┐ ┌──────▼─────┐ ┌───▼────────┐ ┌──▼──────────┐
     │  数据画像   │ │  趋势分析   │ │  异常检测   │ │  投资分析   │
     │   智能体    │ │   智能体    │ │   智能体    │ │   智能体    │
     └────────┬───┘ └──────┬─────┘ └───┬────────┘ └──┬──────────┘
              │            │            │              │
              └────────────┼────────────┼──────────────┘
                           │            │
                  ┌────────▼────────────▼┐
                  │     报告生成器        │
                  └────────┬─────────────┘
                           │
                  ┌────────▼────────┐
                  │   HTML 报告     │
                  └─────────────────┘
```

### 投资分析智能体（asset-lens）

当输入 CSV 为 asset-lens 输出文件（`投资收益率分析_*.csv`）时，投资分析智能体会自动：

- **检测** asset-lens 格式（通过列名关键词：收益率、IRR、年化等）
- **计算** 收益率分布（亏损/0-2%/2-5%/5-10%/10-20%/20%+）
- **评估** 投资组合风险（低收益产品、亏损产品）
- **生成** LLM 驱动的投资洞察（健康评估、调仓建议）
- **可视化** 收益率分布饼图、收益统计柱状图、风险评估图

## 项目结构

```
langgraph-csv-analyst/
├── src/langgraph_csv_analyst/
│   ├── __init__.py          # 包初始化及版本
│   ├── config.py            # 配置（pydantic-settings）
│   ├── csv_parser.py        # CSV 解析与画像
│   ├── agents.py            # 多智能体定义
│   ├── graph.py             # LangGraph 状态图
│   ├── visualization.py     # Plotly 图表生成
│   ├── api.py               # FastAPI 服务
│   └── cli.py               # 命令行工具（Typer）
├── tests/
│   ├── __init__.py
│   └── test_csv_parser.py   # CSV 解析器测试
├── pyproject.toml
├── .env.example
├── .gitignore
├── Makefile
├── README.md
└── README.zh-CN.md
```

## 快速开始

### 1. 安装依赖

```bash
cd invest-kit/apps/langgraph-csv-analyst
uv sync
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OPENAI_API_KEY
```

### 3. 运行分析

```bash
# 完整分析并生成 HTML 报告
uv run langgraph-analyst analyze sample.csv

# 快速数据画像
uv run langgraph-analyst profile sample.csv

# 启动 API 服务
uv run langgraph-analyst-api
```

或使用 Make：

```bash
make install
make analyze FILE=sample.csv
make profile FILE=sample.csv
make api
```

## API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/v1/analyze` | 上传 CSV 并运行完整分析 |
| `GET` | `/api/v1/report/{task_id}` | 获取分析报告 |
| `GET` | `/api/v1/health` | 健康检查 |

### 示例：上传并分析

```bash
curl -X POST "http://localhost:8001/api/v1/analyze" \
  -F "file=@sample.csv"
```

### 示例：获取报告

```bash
curl "http://localhost:8001/api/v1/report/{task_id}"
```

## 配置

所有设置通过 pydantic-settings 从 `.env` 文件加载：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEFAULT_MODEL` | `deepseek-chat` | LLM 模型名称 |
| `OPENAI_API_KEY` | - | OpenAI 兼容 API 密钥 |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | API 基础 URL |
| `CSV_MAX_SIZE_MB` | `50` | CSV 文件最大大小（MB） |
| `MAX_ROWS_DISPLAY` | `100` | 最大显示行数 |
| `API_HOST` | `0.0.0.0` | API 服务主机 |
| `API_PORT` | `8001` | API 服务端口 |
| `DEBUG` | `False` | 调试模式 |

## LangGraph 状态图

分析流水线基于 LangGraph `StateGraph` 构建，流程如下：

1. **load_csv** - 加载并验证 CSV 文件
2. **profile** - 画像数据类型、统计信息和空值计数
3. **并行执行**：
   - **trend_analyzer** - 使用 LLM 分析趋势和模式
   - **anomaly_detector** - 使用 IQR 方法 + LLM 分析检测异常值
4. **generate_report** - 将所有结果编译为 HTML 报告

`AnalysisState` TypedDict 跟踪以下字段：

```python
class AnalysisState(TypedDict, total=False):
    csv_path: str              # 输入 CSV 文件路径
    dataframe_info: dict       # 形状、列名、数据类型
    profile: dict              # 完整数据画像
    trends: dict               # 趋势分析结果
    anomalies: dict            # 异常检测结果
    report: str                # 生成的 HTML 报告
    errors: list[str]          # 收集的错误
```

错误处理通过条件边集成，当任何阶段检测到错误时，路由到 `error_handler` 节点。

## 许可证

MIT
