"""
SENTINEL AI - Explainable Sensor Trust Engine
Calculates transparent, formulaic 0-100 operational trust scores with evidence breakdowns.
"""
from typing import Dict, List, Optional, Tuple, Any
from app.config import settings


class TrustEngine:
    """Operational trust engine evaluating sensor credibility in SCADA networks."""

    def __init__(self,
                 w_ml: float = settings.WEIGHT_ML_ANOMALY,
                 w_inconsistency: float = settings.WEIGHT_INCONSISTENCY,
                 w_sudden: float = settings.WEIGHT_SUDDEN_CHANGE,
                 w_flatline: float = settings.WEIGHT_FLATLINE,
                 recovery_rate: float = settings.TRUST_RECOVERY_RATE):
        self.w_ml = w_ml
        self.w_inconsistency = w_inconsistency
        self.w_sudden = w_sudden
        self.w_flatline = w_flatline
        self.recovery_rate = recovery_rate
        # In-memory sensor trust state: sensor_id -> score
        self.trust_states: Dict[str, float] = {}
        self.consecutive_normal_steps: Dict[str, int] = {}

    def get_status_label(self, score: float) -> str:
        """Maps numerical trust score to operational category."""
        if score >= settings.TRUST_THRESHOLD_TRUSTED:
            return "Trusted"
        elif score >= settings.TRUST_THRESHOLD_MODERATE:
            return "Moderate"
        elif score >= settings.TRUST_THRESHOLD_SUSPICIOUS:
            return "Suspicious"
        else:
            return "Critical"

    def compute_trust_step(self,
                           sensor_id: str,
                           ml_anomaly_score: float = 0.0,
                           inconsistency_score: float = 0.0,
                           rate_violation: bool = False,
                           flatline_detected: bool = False,
                           statistical_anomaly: bool = False,
                           current_trust: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculates one update step for a sensor's trust score.
        Formula:
          Total Penalty = w_ml * ml_score + w_inconsist * inconsist_score + w_sudden * (rate) + w_freeze * (freeze)
          New Trust = Current Trust - Total Penalty (or + Recovery if clean)
        """
        score = current_trust if current_trust is not None else self.trust_states.get(sensor_id, 100.0)
        
        penalties = {}
        evidence = []

        # 1. ML Anomaly Penalty
        if ml_anomaly_score > 0.4:
            p_ml = self.w_ml * ml_anomaly_score
            penalties["ml_anomaly_penalty"] = round(p_ml, 2)
            evidence.append(f"ML Isolation Forest detected outlier behavior (score: {ml_anomaly_score:.2f})")
        else:
            penalties["ml_anomaly_penalty"] = 0.0

        # 2. Cross-Sensor Inconsistency Penalty
        if inconsistency_score > 0.0:
            p_inconsist = self.w_inconsistency * inconsistency_score
            penalties["inconsistency_penalty"] = round(p_inconsist, 2)
            evidence.append(f"Physical/topological contradiction with coupled sensors (inconsistency: {inconsistency_score:.2f})")
        else:
            penalties["inconsistency_penalty"] = 0.0

        # 3. Sudden Rate-of-Change Violation
        if rate_violation:
            p_sudden = self.w_sudden
            penalties["rate_violation_penalty"] = round(p_sudden, 2)
            evidence.append("Instantaneous gradient violates hydraulic rate-of-change limits")
        else:
            penalties["rate_violation_penalty"] = 0.0

        # 4. Signal Freeze / Flatline Penalty
        if flatline_detected:
            p_flat = self.w_flatline
            penalties["flatline_penalty"] = round(p_flat, 2)
            evidence.append("Signal flatline detected: sensor reporting frozen value despite dynamic load")
        else:
            penalties["flatline_penalty"] = 0.0

        total_penalty = sum(penalties.values())

        if total_penalty > 0:
            new_score = max(0.0, score - total_penalty)
            self.consecutive_normal_steps[sensor_id] = 0
        else:
            # Gradual trust recovery
            steps = self.consecutive_normal_steps.get(sensor_id, 0) + 1
            self.consecutive_normal_steps[sensor_id] = steps
            recovery = min(self.recovery_rate * (1 + 0.1 * steps), 10.0)
            new_score = min(100.0, score + recovery)
            evidence.append(f"Clean operational window (+{recovery:.1f} trust recovery)")

        new_score = round(new_score, 1)
        self.trust_states[sensor_id] = new_score
        status_label = self.get_status_label(new_score)

        return {
            "sensor_id": sensor_id,
            "previous_score": score,
            "trust_score": new_score,
            "status": status_label,
            "total_penalty": round(total_penalty, 2),
            "penalties": penalties,
            "evidence": evidence,
            "is_trusted": new_score >= settings.TRUST_THRESHOLD_TRUSTED
        }

    def reset_sensor(self, sensor_id: str):
        """Resets a sensor's trust score to baseline 100."""
        self.trust_states[sensor_id] = 100.0
        self.consecutive_normal_steps[sensor_id] = 0
