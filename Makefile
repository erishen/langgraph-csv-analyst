.PHONY: help install test clean run format lint all sync \
        api analyze profile version

.DEFAULT_GOAL := help

BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help:
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo "$(GREEN)  LangGraph CSV Analyst Makefile (uv)$(RESET)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════════$(RESET)"
	@echo ""
	@echo "$(YELLOW)Usage:$(RESET) make [target]"
	@echo ""
	@echo "$(BLUE)Setup$(RESET)"
	@echo "  install         Install project dependencies"
	@echo "  sync            Sync dependencies to virtual environment"
	@echo "  env             Create .env file from .env.example"
	@echo "  all             Full setup (clean + install + config)"
	@echo ""
	@echo "$(BLUE)Testing$(RESET)"
	@echo "  test            Run all tests"
	@echo "  test-coverage   Run tests with coverage report"
	@echo ""
	@echo "$(BLUE)Running$(RESET)"
	@echo "  analyze         Analyze a CSV file (requires FILE var)"
	@echo "  profile         Quick profile a CSV file (requires FILE var)"
	@echo "  version         Show version"
	@echo ""
	@echo "$(BLUE)API Server$(RESET)"
	@echo "  api             Start FastAPI server"
	@echo ""
	@echo "$(BLUE)Code Quality$(RESET)"
	@echo "  format          Format code with ruff"
	@echo "  lint            Lint code with ruff"
	@echo "  check           Run all checks (format + lint)"
	@echo ""
	@echo "$(BLUE)Cleanup$(RESET)"
	@echo "  clean           Clean cache and temp files"
	@echo "  clean-all       Deep clean (including venv)"
	@echo ""
	@echo "$(BLUE)Examples:$(RESET)"
	@echo "  make install"
	@echo "  make analyze FILE=sample.csv"
	@echo "  make profile FILE=sample.csv"
	@echo ""

# ═══════════════════════════════════════════════════════════
# Setup
# ═══════════════════════════════════════════════════════════

install:
	@echo "$(GREEN)Installing project dependencies...$(RESET)"
	uv sync
	@echo "$(GREEN)Done!$(RESET)"

sync:
	@echo "$(GREEN)Syncing dependencies...$(RESET)"
	uv sync
	@echo "$(GREEN)Done!$(RESET)"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env file, please edit and set your API key$(RESET)"; \
	else \
		echo "$(YELLOW).env file already exists$(RESET)"; \
	fi

all: clean install env
	@echo "$(GREEN)Setup complete!$(RESET)"
	@echo "$(YELLOW)Please edit .env and set your API key$(RESET)"

# ═══════════════════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════════════════

test:
	@echo "$(GREEN)Running all tests...$(RESET)"
	uv run pytest -v
	@echo "$(GREEN)Tests complete!$(RESET)"

test-coverage:
	@echo "$(GREEN)Running tests with coverage...$(RESET)"
	uv run pytest --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

# ═══════════════════════════════════════════════════════════
# Running
# ═══════════════════════════════════════════════════════════

analyze:
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please provide FILE variable$(RESET)"; \
		echo "Usage: make analyze FILE=sample.csv"; \
		exit 1; \
	fi
	@echo "$(GREEN)Analyzing CSV file...$(RESET)"
	uv run langgraph-analyst analyze "$(FILE)"

profile:
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please provide FILE variable$(RESET)"; \
		echo "Usage: make profile FILE=sample.csv"; \
		exit 1; \
	fi
	@echo "$(GREEN)Profiling CSV file...$(RESET)"
	uv run langgraph-analyst profile "$(FILE)"

version:
	uv run langgraph-analyst version

# ═══════════════════════════════════════════════════════════
# API Server
# ═══════════════════════════════════════════════════════════

api:
	@echo "$(GREEN)Starting FastAPI server...$(RESET)"
	@echo "$(YELLOW)API: http://localhost:8001$(RESET)"
	@echo "$(YELLOW)Docs: http://localhost:8001/docs$(RESET)"
	uv run langgraph-analyst-api

# ═══════════════════════════════════════════════════════════
# Code Quality
# ═══════════════════════════════════════════════════════════

format:
	@echo "$(GREEN)Formatting code...$(RESET)"
	uv run ruff format .
	@echo "$(GREEN)Done!$(RESET)"

lint:
	@echo "$(GREEN)Linting code...$(RESET)"
	uv run ruff check .
	@echo "$(GREEN)Done!$(RESET)"

check: format lint
	@echo "$(GREEN)All checks complete!$(RESET)"

# ═══════════════════════════════════════════════════════════
# Cleanup
# ═══════════════════════════════════════════════════════════

clean:
	@echo "$(GREEN)Cleaning cache and temp files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache 2>/dev/null || true
	rm -rf .mypy_cache 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf htmlcov 2>/dev/null || true
	@echo "$(GREEN)Done!$(RESET)"

clean-all: clean
	@echo "$(GREEN)Deep cleaning (including venv)...$(RESET)"
	rm -rf .venv 2>/dev/null || true
	@echo "$(GREEN)Done!$(RESET)"
