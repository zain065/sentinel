"""
SENTINEL AI - REST API Routes
FastAPI endpoints for dataset status, anomaly detection, sensor trust, FDI simulation, and alerts.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd

from app.config import settings, BATADAL_SENSORS, TOPOLOGICAL_COUPLES
from app.database.db import get_db, SensorRecord, SecurityAlert, SimulationLog, TrustHistory
from app.data.batadal_loader import BatadalLoader
from app.data.validation import DataValidator
from app.data.preprocessing import PreprocessingPipeline
from app.models.isolation_forest import IsolationForestDetector
from app.models.statistical_detector import StatisticalDetector
from app.detection.consistency import ConsistencyVerifier
from app.detection.attack_simulator import AttackSimulator
from app.trust.trust_engine import TrustEngine
from app.analysis.impact_analysis import ImpactAnalysisEngine
from app.models.evaluation import ModelEvaluator

router = APIRouter()

# Global in-memory components
loader = BatadalLoader()
validator = DataValidator()
trust_engine = TrustEngine()
stat_detector = StatisticalDetector()
consistency_verifier = ConsistencyVerifier()


# Pydantic Schemas
class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: str


class DetectionRequest(BaseModel):
    sensor_id: str
    telemetry_window: List[float] = Field(..., min_items=2)
    coupled_readings: Optional[Dict[str, float]] = None


class SimulationRequest(BaseModel):
    sensor_id: str
    attack_type: str = Field(..., pattern="^(value_manipulation|constant_value|replay_attack|gradual_drift)$")
    start_index: int = Field(default=10, ge=0)
    duration_steps: int = Field(default=20, ge=1, le=200)
    intensity: float = Field(default=1.5, ge=0.1, le=10.0)


# 1. Health Endpoint
@router.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# 2. Dataset Status & Inspection
@router.get("/dataset/status")
def get_dataset_status():
    """Reports status of dataset files on disk without inventing or downloading anything."""
    return loader.get_dataset_status()


@router.post("/dataset/inspect")
async def inspect_uploaded_csv(file: UploadFile = File(...)):
    """Accepts an uploaded CSV file and returns its schema, missing values, and columns."""
    try:
        df = pd.read_csv(file.file)
        df = validator.clean_columns(df)
        df, ts_col = validator.parse_timestamps(df)
        info = validator.inspect_dataframe(df)
        info["timestamp_column_identified"] = ts_col
        info["filename"] = file.filename
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to inspect CSV file: {str(e)}")


# 3. Sensors & Trust Monitoring
@router.get("/sensors")
def list_sensors(db: Session = Depends(get_db)):
    """Returns all network sensors with their current readings and trust states."""
    sensors_list = []
    for s_id, meta in BATADAL_SENSORS.items():
        score = trust_engine.trust_states.get(s_id, 100.0)
        status = trust_engine.get_status_label(score)
        sensors_list.append({
            "sensor_id": s_id,
            "type": meta["type"],
            "unit": meta["unit"],
            "description": meta["desc"],
            "current_reading": None,
            "trust_score": score,
            "status": status,
            "coupled_peers": TOPOLOGICAL_COUPLES.get(s_id, [])
        })
    return {
        "total_sensors": len(sensors_list),
        "trusted_count": sum(1 for s in sensors_list if s["status"] == "Trusted"),
        "moderate_count": sum(1 for s in sensors_list if s["status"] == "Moderate"),
        "suspicious_count": sum(1 for s in sensors_list if s["status"] == "Suspicious"),
        "critical_count": sum(1 for s in sensors_list if s["status"] == "Critical"),
        "sensors": sensors_list
    }


@router.get("/sensors/{sensor_id}")
def get_sensor_detail(sensor_id: str):
    """Returns detailed configuration and topology for a specific sensor."""
    if sensor_id not in BATADAL_SENSORS:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found in network.")
    
    meta = BATADAL_SENSORS[sensor_id]
    score = trust_engine.trust_states.get(sensor_id, 100.0)
    return {
        "sensor_id": sensor_id,
        "metadata": meta,
        "trust_score": score,
        "status": trust_engine.get_status_label(score),
        "coupled_sensors": TOPOLOGICAL_COUPLES.get(sensor_id, []),
    }


# 4. Anomaly Detection
@router.post("/detection/run")
def run_detection(payload: DetectionRequest):
    """Executes multi-tier anomaly detection (Statistical + Consistency + Trust Step)."""
    series = pd.Series(payload.telemetry_window)
    stat_result = stat_detector.analyze_sensor(payload.sensor_id, series)

    # Cross-sensor consistency check if coupled readings were passed
    consistency_result = {"is_consistent": True, "inconsistency_score": 0.0, "discrepancies": []}
    if payload.coupled_readings:
        coupled_dict = dict(payload.coupled_readings)
        coupled_dict[payload.sensor_id] = float(series.iloc[-1])
        consistency_result = consistency_verifier.verify_sensor(payload.sensor_id, coupled_dict)

    # Trust update
    trust_result = trust_engine.compute_trust_step(
        sensor_id=payload.sensor_id,
        ml_anomaly_score=0.7 if stat_result["is_anomalous"] else 0.0,
        inconsistency_score=consistency_result["inconsistency_score"],
        rate_violation=stat_result["rate_violation"],
        flatline_detected=stat_result["is_frozen"],
        statistical_anomaly=stat_result["is_zscore_anom"]
    )

    alert = None
    if trust_result["trust_score"] < settings.TRUST_THRESHOLD_SUSPICIOUS:
        alert = ImpactAnalysisEngine.evaluate_impact(
            sensor_id=payload.sensor_id,
            observed_val=float(series.iloc[-1]),
            expected_val=float(series.mean()),
            trust_score=trust_result["trust_score"],
            reasons=stat_result["reasons"] + consistency_result["discrepancies"],
            detection_methods=["Statistical", "Consistency"]
        )

    return {
        "sensor_id": payload.sensor_id,
        "latest_reading": float(series.iloc[-1]),
        "statistical_checks": stat_result,
        "consistency_checks": consistency_result,
        "trust_evaluation": trust_result,
        "generated_alert": alert
    }


# 5. Synthetic FDI Attack Simulation
@router.post("/simulation/inject")
def simulate_attack(payload: SimulationRequest):
    """
    Applies synthetic FDI attack onto sample or loaded data and analyzes detection response.
    Does NOT alter stored dataset files.
    """
    # Create sample synthetic baseline segment if raw file not yet loaded
    t = np.linspace(0, 10 * np.pi, 100)
    baseline_val = 5.0 + 3.0 * np.sin(t) + np.random.normal(0, 0.2, 100)
    df_sample = pd.DataFrame({payload.sensor_id: baseline_val})

    sim_result = AttackSimulator.inject_attack(
        data_df=df_sample,
        sensor_id=payload.sensor_id,
        attack_type=payload.attack_type,
        start_index=payload.start_index,
        duration_steps=payload.duration_steps,
        intensity=payload.intensity
    )

    # Run detection on manipulated series to measure latency and detection rate
    manipulated_series = pd.Series(sim_result["simulated_dataframe"][payload.sensor_id])
    detected_steps = []
    
    # Reset sensor trust for clean benchmark
    temp_trust = 100.0
    trust_history = []
    
    for idx in range(payload.start_index, payload.start_index + payload.duration_steps):
        window = manipulated_series.iloc[max(0, idx - 12): idx + 1]
        stat_eval = stat_detector.analyze_sensor(payload.sensor_id, window)
        t_step = trust_engine.compute_trust_step(
            sensor_id=payload.sensor_id,
            ml_anomaly_score=0.8 if stat_eval["is_anomalous"] else 0.0,
            inconsistency_score=0.5 if stat_eval["is_anomalous"] else 0.0,
            rate_violation=stat_eval["rate_violation"],
            flatline_detected=stat_eval["is_frozen"],
            current_trust=temp_trust
        )
        temp_trust = t_step["trust_score"]
        trust_history.append({"step": idx, "trust": temp_trust})
        if stat_eval["is_anomalous"] or temp_trust < 60.0:
            detected_steps.append(idx)

    first_det = (detected_steps[0] - payload.start_index) if detected_steps else None

    return {
        "simulation_parameters": {
            "sensor_id": payload.sensor_id,
            "attack_type": payload.attack_type,
            "start_index": payload.start_index,
            "duration": payload.duration_steps,
            "intensity": payload.intensity
        },
        "detection_benchmark": {
            "was_detected": len(detected_steps) > 0,
            "detection_latency_steps": first_det,
            "detected_points_count": len(detected_steps),
            "final_trust_score": temp_trust,
            "status": trust_engine.get_status_label(temp_trust)
        },
        "original_series": sim_result["original_series"],
        "manipulated_series": sim_result["manipulated_series"],
        "trust_history": trust_history
    }


# 6. Security Alerts
@router.get("/alerts")
def get_security_alerts(db: Session = Depends(get_db)):
    """Returns active and historical security alerts."""
    alerts = db.query(SecurityAlert).order_by(SecurityAlert.timestamp.desc()).limit(50).all()
    return {
        "total_alerts": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "sensor_id": a.sensor_id,
                "timestamp": a.timestamp.isoformat(),
                "severity": a.severity,
                "alert_type": a.alert_type,
                "trust_score": a.trust_score,
                "evidence": a.evidence,
                "recommended_action": a.recommended_action,
                "is_acknowledged": a.is_acknowledged
            }
            for a in alerts
        ]
    }


# 7. Topology Graph
@router.get("/topology")
def get_network_topology():
    """Returns C-Town water network nodes and topological links for network visualization."""
    nodes = []
    edges = []

    for s_id, meta in BATADAL_SENSORS.items():
        nodes.append({
            "id": s_id,
            "label": s_id,
            "type": meta["type"],
            "unit": meta["unit"],
            "trust_score": trust_engine.trust_states.get(s_id, 100.0)
        })

    for source, targets in TOPOLOGICAL_COUPLES.items():
        for target in targets:
            edges.append({
                "source": source,
                "target": target
            })

    return {
        "network": "C-Town Water Distribution Network (BATADAL)",
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "nodes": nodes,
        "edges": edges
    }
