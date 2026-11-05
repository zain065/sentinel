"""
SENTINEL AI - Impact Analysis & Security Alerts Engine
Generates context-aware security alerts and operator decision-support recommendations.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from app.config import TOPOLOGICAL_COUPLES, BATADAL_SENSORS


class ImpactAnalysisEngine:
    """Evaluates cyber-physical impact of corrupted telemetry and generates operator guidance."""

    @staticmethod
    def evaluate_impact(sensor_id: str,
                        observed_val: float,
                        expected_val: Optional[float],
                        trust_score: float,
                        reasons: List[str],
                        detection_methods: List[str]) -> Dict[str, Any]:
        """Produces a comprehensive security alert with technical evidence and actionable advice."""
        sensor_meta = BATADAL_SENSORS.get(sensor_id, {"type": "unknown", "unit": "units", "desc": sensor_id})
        coupled_peers = TOPOLOGICAL_COUPLES.get(sensor_id, [])

        # Determine alert severity based on trust score
        if trust_score < 40.0:
            severity = "Critical"
        elif trust_score < 60.0:
            severity = "High"
        elif trust_score < 80.0:
            severity = "Medium"
        else:
            severity = "Low"

        # Hydraulic impact assessment based on sensor physical role
        s_type = sensor_meta.get("type", "unknown")
        impact_summary = "Minor operational variance"
        recommended_action = "Continue monitoring telemetry trends."

        if s_type == "level":
            # Tank water level
            if expected_val is not None and observed_val < expected_val:
                impact_summary = (
                    f"Under-reporting tank level ({observed_val:.2f}{sensor_meta['unit']}): "
                    f"Risk of automated pump over-activation causing overflow or pipe pressure surge."
                )
            else:
                impact_summary = (
                    f"Over-reporting tank level: Risk of false pump cut-off leading to distribution supply deficit."
                )
            recommended_action = (
                f"1. Manually verify water level at Tank '{sensor_id}'.\n"
                f"2. Temporarily isolate '{sensor_id}' telemetry from SCADA control loops.\n"
                f"3. Infer operational tank volume using coupled pump telemetry ({', '.join(coupled_peers)})."
            )

        elif s_type == "pressure":
            impact_summary = (
                f"Anomalous junction pressure ({observed_val:.2f}{sensor_meta['unit']}): "
                f"May mask burst mains, leakages, or induce false valve throttling."
            )
            recommended_action = (
                f"1. Cross-reference pressure readings with adjacent junctions ({', '.join(coupled_peers)}).\n"
                f"2. Dispatch field technician to verify transducer calibration."
            )

        elif s_type == "flow":
            impact_summary = (
                f"Flow rate anomaly ({observed_val:.2f}{sensor_meta['unit']}): "
                f"Contradicts pump status and downstream pressure trends."
            )
            recommended_action = (
                f"1. Verify electrical status of pump drive.\n"
                f"2. Check flowmeter signal cabling for hardware tamper or false injection."
            )

        return {
            "sensor_id": sensor_id,
            "sensor_description": sensor_meta.get("desc", sensor_id),
            "sensor_type": s_type,
            "unit": sensor_meta.get("unit", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "observed_value": round(observed_val, 2),
            "expected_value": round(expected_val, 2) if expected_val is not None else None,
            "trust_score": trust_score,
            "status": "Critical" if trust_score < 40 else ("Suspicious" if trust_score < 60 else "Moderate"),
            "detection_methods": detection_methods,
            "evidence": reasons,
            "coupled_sensors": coupled_peers,
            "operational_impact": impact_summary,
            "recommended_action": recommended_action,
            "is_advisory_only": True  # Explicit disclaimer that system advises human operators
        }
