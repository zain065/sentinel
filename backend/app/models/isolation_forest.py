"""
SENTINEL AI - Isolation Forest Anomaly Detection Model
Unsupervised ensemble tree model trained on normal baseline operational behavior.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from app.config import settings


class IsolationForestDetector:
    """Unsupervised Isolation Forest anomaly detector for multi-sensor SCADA networks."""

    def __init__(self,
                 contamination: float = settings.IFOREST_CONTAMINATION,
                 n_estimators: int = settings.IFOREST_N_ESTIMATORS,
                 random_state: int = settings.RANDOM_SEED):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.feature_names: List[str] = []
        self.is_fitted: bool = False
        self.baseline_median: Optional[np.ndarray] = None
        self.baseline_iqr: Optional[np.ndarray] = None

    def fit(self, X: np.ndarray, feature_names: List[str]) -> "IsolationForestDetector":
        """Fits Isolation Forest strictly on baseline operational data."""
        self.feature_names = list(feature_names)
        self.model.fit(X)
        self.is_fitted = True

        # Compute robust centroid and spread for feature contribution estimation
        self.baseline_median = np.median(X, axis=0)
        q75, q25 = np.percentile(X, [75, 25], axis=0)
        iqr = q75 - q25
        self.baseline_iqr = np.where(iqr == 0, 1e-4, iqr)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Returns binary predictions: -1 for anomaly, 1 for normal."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        return self.model.predict(X)

    def anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Converts sklearn decision_function to a normalized anomaly score between 0.0 and 1.0.
        0.0 = completely normal, 1.0 = highly anomalous.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before anomaly_scores.")
        
        # decision_function: lower is more abnormal, negative = anomaly
        raw_scores = self.model.decision_function(X)
        # Apply sigmoid or inverted min-max normalization
        # Typical decision scores range from -0.3 to +0.3
        norm_scores = 1.0 / (1.0 + np.exp(raw_scores * 8.0))
        return np.clip(norm_scores, 0.0, 1.0)

    def explain_anomaly(self, sample: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        """Identifies which sensor features contributed most to the anomaly."""
        if self.baseline_median is None or self.baseline_iqr is None:
            return []
        
        deviations = np.abs(sample - self.baseline_median) / self.baseline_iqr
        top_indices = np.argsort(deviations)[::-1][:top_k]
        
        explanations = []
        for idx in top_indices:
            explanations.append({
                "sensor_id": self.feature_names[idx],
                "robust_z_dev": float(round(deviations[idx], 2)),
                "current_val": float(sample[idx]),
                "expected_median": float(self.baseline_median[idx])
            })
        return explanations

    def save(self, filepath: Optional[Path] = None) -> Path:
        """Saves model artifact to disk."""
        target_path = filepath or (settings.MODELS_DIR / "isolation_forest.joblib")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names,
            "contamination": self.contamination,
            "n_estimators": self.n_estimators,
            "is_fitted": self.is_fitted,
            "baseline_median": self.baseline_median,
            "baseline_iqr": self.baseline_iqr,
        }, target_path)
        return target_path

    @classmethod
    def load(cls, filepath: Optional[Path] = None) -> "IsolationForestDetector":
        """Loads model artifact from disk."""
        target_path = filepath or (settings.MODELS_DIR / "isolation_forest.joblib")
        if not target_path.exists():
            raise FileNotFoundError(f"Model artifact not found at {target_path}")
        
        data = joblib.load(target_path)
        instance = cls(contamination=data["contamination"], n_estimators=data["n_estimators"])
        instance.model = data["model"]
        instance.feature_names = data["feature_names"]
        instance.is_fitted = data["is_fitted"]
        instance.baseline_median = data["baseline_median"]
        instance.baseline_iqr = data["baseline_iqr"]
        return instance
