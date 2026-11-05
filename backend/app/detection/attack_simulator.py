"""
SENTINEL AI - Synthetic FDI Attack Simulator
Generates controlled, synthetic cyber-physical attack scenarios to benchmark detection response.
Does NOT modify original datasets.
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


class AttackSimulator:
    """Simulates 4 distinct False Data Injection (FDI) attack vectors on telemetry streams."""

    ATTACK_TYPES = [
        "value_manipulation",
        "constant_value",
        "replay_attack",
        "gradual_drift"
    ]

    @staticmethod
    def inject_attack(data_df: pd.DataFrame,
                      sensor_id: str,
                      attack_type: str,
                      start_index: int,
                      duration_steps: int,
                      intensity: float = 1.0) -> Dict[str, Any]:
        """
        Injects a synthetic FDI attack onto a copy of the telemetry segment.
        Leaves original dataframe completely untouched.
        """
        if sensor_id not in data_df.columns:
            raise ValueError(f"Sensor '{sensor_id}' not found in dataframe.")
        if attack_type not in AttackSimulator.ATTACK_TYPES:
            raise ValueError(f"Unknown attack type '{attack_type}'. Supported: {AttackSimulator.ATTACK_TYPES}")
        if start_index < 0 or start_index >= len(data_df):
            raise ValueError(f"start_index {start_index} out of bounds (0 to {len(data_df)-1}).")

        # Copy data so original is pristine
        sim_df = data_df.copy()
        n = len(sim_df)
        end_index = min(n, start_index + duration_steps)
        actual_duration = end_index - start_index

        original_values = sim_df[sensor_id].values.copy()
        manipulated_values = original_values.copy()

        attack_indices = list(range(start_index, end_index))

        if attack_type == "value_manipulation":
            # Shifts reading abruptly by intensity * standard deviation or offset
            std_val = float(np.std(original_values)) if np.std(original_values) > 0 else 1.0
            shift = intensity * std_val * 3.5
            manipulated_values[start_index:end_index] += shift

        elif attack_type == "constant_value":
            # Freezes the sensor value at whatever it was immediately prior to the attack
            freeze_val = float(original_values[start_index])
            manipulated_values[start_index:end_index] = freeze_val

        elif attack_type == "replay_attack":
            # Replaces current telemetry with a stale window from earlier in the timeline
            replay_lag = max(duration_steps, 24)
            if start_index >= replay_lag:
                replay_source = original_values[start_index - replay_lag: start_index - replay_lag + actual_duration]
                manipulated_values[start_index:end_index] = replay_source[:actual_duration]
            else:
                # If not enough history, use shifted mirror
                manipulated_values[start_index:end_index] = original_values[0:actual_duration]

        elif attack_type == "gradual_drift":
            # Progressively ramps value upwards or downwards
            ramp = np.linspace(0, intensity * 2.0, actual_duration)
            manipulated_values[start_index:end_index] += ramp

        sim_df[sensor_id] = manipulated_values

        return {
            "is_synthetic_simulation": True,
            "sensor_id": sensor_id,
            "attack_type": attack_type,
            "start_index": start_index,
            "end_index": end_index,
            "duration_steps": actual_duration,
            "intensity": intensity,
            "simulated_dataframe": sim_df,
            "original_series": original_values[start_index - 5: end_index + 5].tolist() if start_index >= 5 else original_values[:end_index + 5].tolist(),
            "manipulated_series": manipulated_values[start_index - 5: end_index + 5].tolist() if start_index >= 5 else manipulated_values[:end_index + 5].tolist(),
            "attack_indices": attack_indices
        }

