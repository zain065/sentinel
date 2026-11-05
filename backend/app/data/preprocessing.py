"""
SENTINEL AI - Preprocessing Pipeline
Leakage-free feature scaling, chronological windowing, and sensor feature extraction.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, RobustScaler
from app.config import settings


class PreprocessingPipeline:
    """End-to-end preprocessing pipeline for sensor time-series data."""

    def __init__(self, scaler_type: str = "standard"):
        self.scaler_type = scaler_type
        self.scaler = StandardScaler() if scaler_type == "standard" else RobustScaler()
        self.feature_columns: List[str] = []
        self.is_fitted: bool = False
        self.sensor_stats: Dict[str, Dict[str, float]] = {}

    def get_sensor_columns(self, df: pd.DataFrame) -> List[str]:
        """Filters out non-sensor columns like DATETIME and ATT_FLAG."""
        exclude = ["DATETIME", "datetime", "DateTime", "time", "TIME", "Timestamp", "timestamp", "ATT_FLAG", "att_flag", "Attack", "label"]
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return [c for c in numeric_cols if c not in exclude]

    def fit(self, train_df: pd.DataFrame) -> "PreprocessingPipeline":
        """Fits scaler strictly on normal training data to avoid data leakage."""
        self.feature_columns = self.get_sensor_columns(train_df)
        if not self.feature_columns:
            raise ValueError("No numeric sensor columns found for preprocessing.")

        X = train_df[self.feature_columns].values
        self.scaler.fit(X)
        self.is_fitted = True

        # Compute sensor-wise descriptive statistics for baseline
        self.sensor_stats = {}
        for col in self.feature_columns:
            series = train_df[col].dropna()
            self.sensor_stats[col] = {
                "mean": float(series.mean()),
                "std": float(series.std()) if float(series.std()) > 1e-6 else 1e-6,
                "min": float(series.min()),
                "max": float(series.max()),
                "p25": float(series.quantile(0.25)),
                "p50": float(series.quantile(0.50)),
                "p75": float(series.quantile(0.75)),
                "max_hourly_delta": float(series.diff().abs().max()) if len(series) > 1 else 1.0
            }
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Scales feature matrix using the fitted parameters."""
        if not self.is_fitted:
            raise RuntimeError("PreprocessingPipeline must be fitted before calling transform.")
        
        # Verify required columns exist
        missing = [c for c in self.feature_columns if c not in df.columns]
        if missing:
            raise ValueError(f"Input dataframe missing expected sensor columns: {missing}")

        X = df[self.feature_columns].values
        return self.scaler.transform(X)

    def fit_transform(self, train_df: pd.DataFrame) -> np.ndarray:
        """Fits on train dataframe and returns transformed matrix."""
        return self.fit(train_df).transform(train_df)

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Serializes the fitted pipeline to disk."""
        target_path = filepath or (settings.MODELS_DIR / "preprocessing_pipeline.joblib")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "scaler": self.scaler,
            "scaler_type": self.scaler_type,
            "feature_columns": self.feature_columns,
            "is_fitted": self.is_fitted,
            "sensor_stats": self.sensor_stats,
        }, target_path)
        return target_path

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "PreprocessingPipeline":
        """Loads a serialized pipeline."""
        target_path = filepath or (settings.MODELS_DIR / "preprocessing_pipeline.joblib")
        if not target_path.exists():
            raise FileNotFoundError(f"Fitted preprocessing pipeline not found at {target_path}")
        
        data = joblib.load(target_path)
        instance = cls(scaler_type=data["scaler_type"])
        instance.scaler = data["scaler"]
        instance.feature_columns = data["feature_columns"]
        instance.is_fitted = data["is_fitted"]
        instance.sensor_stats = data["sensor_stats"]
        return instance

