"""CSV parsing and profiling module."""

from __future__ import annotations

import os
from pathlib import Path

import chardet
import pandas as pd

from langgraph_csv_analyst.config import settings


def load_csv(file_path: str | Path) -> pd.DataFrame:
    """Load a CSV file with automatic encoding detection.

    Args:
        file_path: Path to the CSV file.

    Returns:
        A pandas DataFrame with the CSV data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file exceeds the size limit or cannot be parsed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > settings.CSV_MAX_SIZE_MB:
        raise ValueError(
            f"File size ({file_size_mb:.1f} MB) exceeds limit "
            f"({settings.CSV_MAX_SIZE_MB} MB)"
        )

    encoding = _detect_encoding(path)

    try:
        df = pd.read_csv(path, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="utf-8", errors="replace")

    return df


def _detect_encoding(file_path: Path) -> str:
    """Detect the encoding of a file using chardet."""
    with open(file_path, "rb") as f:
        raw = f.read(10000)
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8") or "utf-8"


def get_profile(df: pd.DataFrame) -> dict:
    """Generate a data profile for a DataFrame.

    Args:
        df: The DataFrame to profile.

    Returns:
        A dictionary containing column types, null counts, and basic statistics.
    """
    columns = []
    for col in df.columns:
        col_info = {
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(float(df[col].isnull().mean() * 100), 2),
            "unique_count": int(df[col].nunique()),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["stats"] = {
                "mean": round(float(df[col].mean()), 4) if not df[col].isnull().all() else None,
                "std": round(float(df[col].std()), 4) if not df[col].isnull().all() else None,
                "min": float(df[col].min()) if not df[col].isnull().all() else None,
                "max": float(df[col].max()) if not df[col].isnull().all() else None,
                "median": round(float(df[col].median()), 4) if not df[col].isnull().all() else None,
                "q25": round(float(df[col].quantile(0.25)), 4) if not df[col].isnull().all() else None,
                "q75": round(float(df[col].quantile(0.75)), 4) if not df[col].isnull().all() else None,
            }
        else:
            top_values = df[col].value_counts().head(5).to_dict()
            col_info["stats"] = {
                "top_values": {str(k): int(v) for k, v in top_values.items()},
            }
        columns.append(col_info)

    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": columns,
        "memory_usage_mb": round(float(df.memory_usage(deep=True).sum() / (1024 * 1024)), 2),
    }


def detect_anomalies(df: pd.DataFrame) -> dict:
    """Detect anomalies and outliers using the IQR method.

    Args:
        df: The DataFrame to analyze.

    Returns:
        A dictionary with anomaly information per numeric column.
    """
    anomalies: dict = {"columns": {}}
    total_anomalies = 0

    numeric_cols = df.select_dtypes(include="number").columns
    for col in numeric_cols:
        if df[col].isnull().all():
            continue

        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
        outlier_count = int(outlier_mask.sum())

        if outlier_count > 0:
            anomalies["columns"][col] = {
                "outlier_count": outlier_count,
                "outlier_pct": round(float(outlier_count / len(df) * 100), 2),
                "lower_bound": round(float(lower_bound), 4),
                "upper_bound": round(float(upper_bound), 4),
                "iqr": round(float(iqr), 4),
                "outlier_indices": df.index[outlier_mask].tolist()[:50],
            }
            total_anomalies += outlier_count

    anomalies["total_anomalies"] = total_anomalies
    return anomalies


def get_summary(df: pd.DataFrame) -> dict:
    """Get a summary of the DataFrame.

    Args:
        df: The DataFrame to summarize.

    Returns:
        A dictionary with shape, dtypes, and memory usage.
    """
    return {
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "memory_usage_mb": round(float(df.memory_usage(deep=True).sum() / (1024 * 1024)), 2),
        "null_total": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }
