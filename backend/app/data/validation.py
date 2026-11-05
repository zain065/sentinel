"""
SENTINEL AI - Data Validation Module
Validates CSV structures, timestamps, column types, and data integrity.
"""
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np


class DataValidator:
    """Validates SCADA telemetry datasets for proper typing, nulls, and temporal order."""

    @staticmethod
    def inspect_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """Performs initial schema and health inspection on an uploaded or loaded dataframe."""
        info = {
            "num_rows": int(len(df)),
            "num_columns": int(len(df.columns)),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
            "total_missing": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        }
        return info

    @staticmethod
    def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Strips whitespace, quotation marks, and BOM markers from column names."""
        df = df.copy()
        df.columns = [str(c).strip().strip('"').strip("'") for c in df.columns]
        return df

    @staticmethod
    def parse_timestamps(df: pd.DataFrame, timestamp_col: Optional[str] = None) -> Tuple[pd.DataFrame, Optional[str]]:
        """Identifies and parses timestamps into chronological pandas datetime index."""
        df = df.copy()
        
        # Candidate timestamp column names
        candidates = ["DATETIME", "datetime", "DateTime", "time", "TIME", "Timestamp", "timestamp", "Date", "date"]
        matched_col = None

        if timestamp_col and timestamp_col in df.columns:
            matched_col = timestamp_col
        else:
            for c in df.columns:
                if c in candidates or "time" in c.lower() or "date" in c.lower():
                    matched_col = c
                    break

        if matched_col:
            # BATADAL typically formats as 'dd/mm/yy hh' or 'dd/mm/yyyy hh:mm'
            try:
                df[matched_col] = pd.to_datetime(df[matched_col], format="%d/%m/%y %H", errors="coerce")
            except Exception:
                pass

            if df[matched_col].isna().all():
                # Fallback to general parser
                df[matched_col] = pd.to_datetime(df[matched_col], errors="coerce")

            # Check if chronological
            if not df[matched_col].is_monotonic_increasing:
                df = df.sort_values(by=matched_col).reset_index(drop=True)

        return df, matched_col

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, strategy: str = "forward_fill") -> pd.DataFrame:
        """Handles missing telemetry records using forward-fill followed by backward-fill."""
        df = df.copy()
        if strategy == "forward_fill":
            df = df.ffill().bfill()
        elif strategy == "interpolate":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].interpolate(method="linear").ffill().bfill()
        return df
