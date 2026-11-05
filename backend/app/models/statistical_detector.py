"""
SENTINEL AI - Statistical Anomaly Detector
Rolling z-scores, rate-of-change, CUSUM drift detection, and flat-line signal freeze checks.
"""
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from app.config import settings


class StatisticalDetector:
    """Multi-method statistical detector for physical sensor telemetry."""

    def __init__(self,
                 zscore_thresh: float = settings.ZSCORE_THRESHOLD,
                 window_size: int = settings.ROLLING_WINDOW_SIZE,
                 cusum_thresh: float = settings.CUSUM_THRESHOLD,
                 cusum_drift: float = settings.CUSUM_DRIFT,
                 flatline_hours: int = settings.FLATLINE_WINDOW_MIN_HOURS):
        self.zscore_thresh = zscore_thresh
        self.window_size = window_size
        self.cusum_thresh = cusum_thresh
        self.cusum_drift = cusum_drift
        self.flatline_hours = flatline_hours

    def check_flatline(self, series: pd.Series) -> bool:
        """Detects if sensor readings have frozen at a constant value for >= flatline_hours."""
        if len(series) < self.flatline_hours:
            return False
        tail = series.iloc[-self.flatline_hours:]
        # Check standard deviation or unique value count
        return bool(tail.nunique() == 1 and tail.std() == 0.0)

    def check_rate_of_change(self, series: pd.Series, baseline_max_delta: float) -> bool:
        """Detects if instantaneous rate of change exceeds realistic physical limits."""
        if len(series) < 2:
            return False
        delta = abs(series.iloc[-1] - series.iloc[-2])
        threshold = max(baseline_max_delta * settings.RATE_OF_CHANGE_MAX_FACTOR, 1e-4)
        return bool(delta > threshold)

    def check_rolling_zscore(self, series: pd.Series) -> float:
        """Calculates dynamic z-score relative to the rolling historical window."""
        if len(series) < 3:
            return 0.0
        window = series.iloc[-self.window_size:]
        mean = window.mean()
        std = window.std()
        if std == 0.0 or np.isnan(std):
            return 0.0
        z = (series.iloc[-1] - mean) / std
        return float(z)

    def check_cusum(self, series: pd.Series, target_mean: float, target_std: float) -> Tuple[bool, float]:
        """Calculates tabular CUSUM for detecting subtle, persistent mean drift."""
        if len(series) < 3 or target_std <= 0:
            return False, 0.0
        
        s_pos = 0.0
        s_neg = 0.0
        drift = self.cusum_drift * target_std
        h = self.cusum_thresh * target_std

        for val in series.iloc[-min(len(series), 24):]:
            s_pos = max(0.0, s_pos + (val - target_mean) - drift)
            s_neg = max(0.0, s_neg - (val - target_mean) - drift)
            if s_pos > h or s_neg > h:
                return True, max(s_pos, s_neg) / target_std
        return False, max(s_pos, s_neg) / target_std

    def analyze_sensor(self,
                       sensor_id: str,
                       history_series: pd.Series,
                       baseline_stats: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Runs all statistical checks on a sensor's recent telemetry window."""
        stats = baseline_stats or {}
        b_mean = stats.get("mean", history_series.mean() if len(history_series) else 0.0)
        b_std = stats.get("std", history_series.std() if len(history_series) > 1 else 1.0)
        b_delta = stats.get("max_hourly_delta", 1.0)

        is_frozen = self.check_flatline(history_series)
        rate_violation = self.check_rate_of_change(history_series, b_delta)
        zscore = self.check_rolling_zscore(history_series)
        is_zscore_anom = abs(zscore) >= self.zscore_thresh
        cusum_flag, cusum_stat = self.check_cusum(history_series, b_mean, b_std)

        is_anomalous = is_frozen or rate_violation or is_zscore_anom or cusum_flag

        reasons = []
        if is_frozen:
            reasons.append(f"Constant-value freeze detected: identical value across {self.flatline_hours} hours")
        if rate_violation:
            reasons.append("Physical rate-of-change violation: instantaneous step exceeds hydraulic maximum")
        if is_zscore_anom:
            reasons.append(f"High dynamic z-score ({zscore:.2f} > {self.zscore_thresh})")
        if cusum_flag:
            reasons.append(f"Persistent CUSUM mean drift detected (stat={cusum_stat:.2f})")

        return {
            "sensor_id": sensor_id,
            "is_anomalous": is_anomalous,
            "is_frozen": is_frozen,
            "rate_violation": rate_violation,
            "zscore": round(zscore, 2),
            "is_zscore_anom": is_zscore_anom,
            "cusum_drift": cusum_flag,
            "cusum_stat": round(cusum_stat, 2),
            "reasons": reasons
        }
