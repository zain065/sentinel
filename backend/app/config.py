"""
SENTINEL AI - Configuration & Constants
Global configurations, dataset paths, detection thresholds, and trust weights.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict, List, Any


class Settings(BaseSettings):
    # Base paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
    BACKEND_DIR: Path = PROJECT_ROOT / "backend"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    BATADAL_RAW_DIR: Path = RAW_DATA_DIR / "batadal"
    HAI_RAW_DIR: Path = RAW_DATA_DIR / "hai"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = PROJECT_ROOT / "models" / "saved"
    EVALUATION_DIR: Path = PROJECT_ROOT / "evaluation"
    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'sentinel.db'}"

    # Server Settings
    APP_NAME: str = "SENTINEL AI"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    # Trust Score Thresholds (0 - 100)
    TRUST_THRESHOLD_TRUSTED: float = 80.0
    TRUST_THRESHOLD_MODERATE: float = 60.0
    TRUST_THRESHOLD_SUSPICIOUS: float = 40.0
    # < 40 is Critical

    # Trust Engine Penalty Weights
    WEIGHT_ML_ANOMALY: float = 35.0         # Penalty weight for Isolation Forest anomaly score
    WEIGHT_INCONSISTENCY: float = 30.0       # Penalty weight for cross-sensor physical violation
    WEIGHT_SUDDEN_CHANGE: float = 20.0       # Penalty weight for physical rate-of-change violation
    WEIGHT_FLATLINE: float = 15.0            # Penalty weight for frozen / zero-variance signal
    TRUST_RECOVERY_RATE: float = 2.5         # Incremental trust recovery per consecutive normal step

    # Statistical Anomaly Detection Parameters
    ZSCORE_THRESHOLD: float = 3.0            # Standard deviations for dynamic z-score anomaly
    ROLLING_WINDOW_SIZE: int = 12            # 12-hour rolling window for hourly SCADA
    CUSUM_THRESHOLD: float = 4.0             # Cumulative sum deviation threshold
    CUSUM_DRIFT: float = 0.5                 # Allowable slack in CUSUM
    FLATLINE_WINDOW_MIN_HOURS: int = 4       # Consecutive identical values triggering freeze alarm
    RATE_OF_CHANGE_MAX_FACTOR: float = 4.0   # Multiplier over historical max hourly delta

    # Machine Learning Parameters
    IFOREST_CONTAMINATION: float = 0.05      # Prior estimate of anomaly proportion in training data
    IFOREST_N_ESTIMATORS: int = 150
    RANDOM_SEED: int = 42

    class Config:
        case_sensitive = True


settings = Settings()

# BATADAL C-Town Sensor Metadata & Physical Mapping
# Reference: Battle of the Attack Detection Algorithms (C-Town SCADA)
BATADAL_SENSORS = {
    # Tank Water Levels (metres)
    "L_T1": {"type": "level", "unit": "m", "desc": "Water Level in Tank T1", "min": 0.0, "max": 15.0},
    "L_T2": {"type": "level", "unit": "m", "desc": "Water Level in Tank T2", "min": 0.0, "max": 15.0},
    "L_T3": {"type": "level", "unit": "m", "desc": "Water Level in Tank T3", "min": 0.0, "max": 15.0},
    "L_T4": {"type": "level", "unit": "m", "desc": "Water Level in Tank T4", "min": 0.0, "max": 15.0},
    "L_T5": {"type": "level", "unit": "m", "desc": "Water Level in Tank T5", "min": 0.0, "max": 15.0},
    "L_T6": {"type": "level", "unit": "m", "desc": "Water Level in Tank T6", "min": 0.0, "max": 15.0},
    "L_T7": {"type": "level", "unit": "m", "desc": "Water Level in Tank T7", "min": 0.0, "max": 15.0},
    
    # Inlet/Junction Pressures (metres)
    "F_PU1": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 1", "min": 0.0, "max": 400.0},
    "S_PU1": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 1", "min": 0.0, "max": 1.0},
    "F_PU2": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 2", "min": 0.0, "max": 400.0},
    "S_PU2": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 2", "min": 0.0, "max": 1.0},
    "F_PU3": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 3", "min": 0.0, "max": 400.0},
    "S_PU3": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 3", "min": 0.0, "max": 1.0},
    "F_PU4": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 4", "min": 0.0, "max": 400.0},
    "S_PU4": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 4", "min": 0.0, "max": 1.0},
    "F_PU5": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 5", "min": 0.0, "max": 400.0},
    "S_PU5": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 5", "min": 0.0, "max": 1.0},
    "F_PU6": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 6", "min": 0.0, "max": 400.0},
    "S_PU6": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 6", "min": 0.0, "max": 1.0},
    "F_PU7": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 7", "min": 0.0, "max": 400.0},
    "S_PU7": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 7", "min": 0.0, "max": 1.0},
    "F_PU8": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 8", "min": 0.0, "max": 400.0},
    "S_PU8": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 8", "min": 0.0, "max": 1.0},
    "F_PU9": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 9", "min": 0.0, "max": 400.0},
    "S_PU9": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 9", "min": 0.0, "max": 1.0},
    "F_PU10": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 10", "min": 0.0, "max": 400.0},
    "S_PU10": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 10", "min": 0.0, "max": 1.0},
    "F_PU11": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Pump 11", "min": 0.0, "max": 400.0},
    "S_PU11": {"type": "status", "unit": "binary", "desc": "Operating status of Pump 11", "min": 0.0, "max": 1.0},
    
    # Valve Flow and Status
    "F_V2": {"type": "flow", "unit": "L/s", "desc": "Flow rate through Valve V2", "min": 0.0, "max": 200.0},
    "S_V2": {"type": "status", "unit": "binary", "desc": "Operating status of Valve V2", "min": 0.0, "max": 1.0},

    # Junction Pressures (metres)
    "P_J280": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J280", "min": 0.0, "max": 100.0},
    "P_J269": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J269", "min": 0.0, "max": 100.0},
    "P_J300": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J300", "min": 0.0, "max": 100.0},
    "P_J256": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J256", "min": 0.0, "max": 100.0},
    "P_J289": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J289", "min": 0.0, "max": 100.0},
    "P_J415": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J415", "min": 0.0, "max": 100.0},
    "P_J14": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J14", "min": 0.0, "max": 100.0},
    "P_J422": {"type": "pressure", "unit": "m", "desc": "Pressure at Junction J422", "min": 0.0, "max": 100.0},
}

# Physical Topological Coupling in C-Town (EPANET hydraulic dependency mapping)
# Defines which sensors are physically correlated by proximity, pump stations, or tank inlet/outlet
TOPOLOGICAL_COUPLES: Dict[str, List[str]] = {
    "L_T1": ["F_PU1", "F_PU2", "P_J280"],         # Tank 1 fed by Pump Station 1 (PU1, PU2) near J280
    "L_T2": ["F_PU4", "F_PU5", "P_J269"],         # Tank 2 coupled with PU4, PU5
    "L_T3": ["F_PU6", "F_PU7", "P_J300"],         # Tank 3 coupled with PU6, PU7
    "L_T4": ["F_PU8", "F_PU9", "P_J256"],         # Tank 4 coupled with PU8, PU9
    "L_T5": ["F_PU10", "F_PU11", "P_J289"],       # Tank 5 coupled with PU10, PU11
    "L_T6": ["P_J415", "F_V2"],                   # Tank 6 coupled with Valve V2 and J415
    "L_T7": ["P_J14", "P_J422"],                  # Tank 7 pressure zone
    "F_PU1": ["L_T1", "P_J280", "S_PU1"],
    "F_PU2": ["L_T1", "P_J280", "S_PU2"],
    "F_PU4": ["L_T2", "P_J269", "S_PU4"],
    "F_PU6": ["L_T3", "P_J300", "S_PU6"],
    "F_PU8": ["L_T4", "P_J256", "S_PU8"],
    "F_PU10": ["L_T5", "P_J289", "S_PU10"],
}
