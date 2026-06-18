"""Tests for the CSV parser module."""

from __future__ import annotations

import os
import tempfile

import pandas as pd
import pytest

from langgraph_csv_analyst.csv_parser import (
    detect_anomalies,
    get_profile,
    get_summary,
    load_csv,
)


@pytest.fixture
def sample_csv() -> str:
    """Create a temporary CSV file for testing."""
    data = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 40, 100],
        "score": [85.5, 90.0, 78.3, 92.1, 88.7],
        "city": ["NYC", "LA", "NYC", "Chicago", "LA"],
    })
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    data.to_csv(tmp.name, index=False)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def csv_with_nulls() -> str:
    """Create a CSV file with null values."""
    data = pd.DataFrame({
        "col_a": [1, 2, None, 4, 5],
        "col_b": ["x", None, "z", "w", None],
        "col_c": [10.0, 20.0, 30.0, None, 50.0],
    })
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    data.to_csv(tmp.name, index=False)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def csv_with_outliers() -> str:
    """Create a CSV file with clear outliers."""
    values = [10, 12, 11, 13, 10, 12, 11, 14, 10, 1000]
    data = pd.DataFrame({"value": values})
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    data.to_csv(tmp.name, index=False)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


class TestLoadCsv:
    """Tests for load_csv function."""

    def test_load_valid_csv(self, sample_csv: str) -> None:
        """Test loading a valid CSV file."""
        df = load_csv(sample_csv)
        assert len(df) == 5
        assert list(df.columns) == ["name", "age", "score", "city"]

    def test_load_nonexistent_file(self) -> None:
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/path/file.csv")

    def test_load_csv_with_nulls(self, csv_with_nulls: str) -> None:
        """Test loading a CSV with null values."""
        df = load_csv(csv_with_nulls)
        assert df["col_a"].isnull().sum() == 1
        assert df["col_b"].isnull().sum() == 2


class TestGetProfile:
    """Tests for get_profile function."""

    def test_profile_structure(self, sample_csv: str) -> None:
        """Test profile returns expected structure."""
        df = load_csv(sample_csv)
        profile = get_profile(df)

        assert "total_rows" in profile
        assert "total_columns" in profile
        assert "columns" in profile
        assert "memory_usage_mb" in profile

    def test_profile_total_rows(self, sample_csv: str) -> None:
        """Test profile reports correct row count."""
        df = load_csv(sample_csv)
        profile = get_profile(df)
        assert profile["total_rows"] == 5

    def test_profile_column_info(self, sample_csv: str) -> None:
        """Test profile includes column-level information."""
        df = load_csv(sample_csv)
        profile = get_profile(df)

        age_col = next(c for c in profile["columns"] if c["name"] == "age")
        assert age_col["dtype"] == "int64"
        assert "mean" in age_col["stats"]

    def test_profile_with_nulls(self, csv_with_nulls: str) -> None:
        """Test profile correctly reports null counts."""
        df = load_csv(csv_with_nulls)
        profile = get_profile(df)

        col_a = next(c for c in profile["columns"] if c["name"] == "col_a")
        assert col_a["null_count"] == 1
        assert col_a["null_pct"] == 20.0


class TestDetectAnomalies:
    """Tests for detect_anomalies function."""

    def test_detect_outliers(self, csv_with_outliers: str) -> None:
        """Test that outliers are detected using IQR method."""
        df = load_csv(csv_with_outliers)
        anomalies = detect_anomalies(df)

        assert "columns" in anomalies
        assert "total_anomalies" in anomalies
        assert anomalies["total_anomalies"] > 0
        assert "value" in anomalies["columns"]

    def test_no_anomalies_in_uniform_data(self) -> None:
        """Test that uniform data has no anomalies."""
        df = pd.DataFrame({"value": [1, 1, 1, 1, 1]})
        anomalies = detect_anomalies(df)
        assert anomalies["total_anomalies"] == 0

    def test_anomaly_bounds(self, csv_with_outliers: str) -> None:
        """Test that anomaly bounds are reported."""
        df = load_csv(csv_with_outliers)
        anomalies = detect_anomalies(df)

        if "value" in anomalies["columns"]:
            col_info = anomalies["columns"]["value"]
            assert "lower_bound" in col_info
            assert "upper_bound" in col_info
            assert "iqr" in col_info


class TestGetSummary:
    """Tests for get_summary function."""

    def test_summary_structure(self, sample_csv: str) -> None:
        """Test summary returns expected structure."""
        df = load_csv(sample_csv)
        summary = get_summary(df)

        assert "shape" in summary
        assert "dtypes" in summary
        assert "memory_usage_mb" in summary
        assert "null_total" in summary
        assert "duplicate_rows" in summary

    def test_summary_shape(self, sample_csv: str) -> None:
        """Test summary reports correct shape."""
        df = load_csv(sample_csv)
        summary = get_summary(df)
        assert summary["shape"]["rows"] == 5
        assert summary["shape"]["columns"] == 4

    def test_summary_with_nulls(self, csv_with_nulls: str) -> None:
        """Test summary reports null count."""
        df = load_csv(csv_with_nulls)
        summary = get_summary(df)
        assert summary["null_total"] == 4
