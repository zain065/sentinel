"""
SENTINEL AI - Sensor Relationship & Topological Consistency Verifier
Verifies physical and correlation consistency across connected sensor clusters in the water network.
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from app.config import TOPOLOGICAL_COUPLES, BATADAL_SENSORS


class ConsistencyVerifier:
    """Verifies that topologically and physically coupled sensors agree with each other."""

    def __init__(self, topology_mapping: Optional[Dict[str, List[str]]] = None):
        self.topology = topology_mapping or TOPOLOGICAL_COUPLES
        self.learned_correlations: Dict[str, Dict[str, float]] = {}
        self.learned_ratios: Dict[Tuple[str, str], Dict[str, float]] = {}

    def fit_baseline_relationships(self, normal_df: pd.DataFrame):
        """Learns baseline cross-sensor correlations and expected ratios on normal data."""
        # Calculate full correlation matrix
        numeric_df = normal_df.select_dtypes(include=[np.number])
        corr_matrix = numeric_df.corr(method="pearson").fillna(0.0)

        for sensor, coupled_list in self.topology.items():
            if sensor not in numeric_df.columns:
                continue
            self.learned_correlations[sensor] = {}
            for peer in coupled_list:
                if peer in numeric_df.columns:
                    corr_val = float(corr_matrix.loc[sensor, peer])
                    self.learned_correlations[sensor][peer] = round(corr_val, 3)

                    # Learn normal relative ratio statistics if both sensors have non-zero means
                    s_mean = float(numeric_df[sensor].mean())
                    p_mean = float(numeric_df[peer].mean())
                    if abs(p_mean) > 1e-3:
                        ratio_series = (numeric_df[sensor] / (numeric_df[peer] + 1e-4)).dropna()
                        self.learned_ratios[(sensor, peer)] = {
                            "ratio_mean": float(ratio_series.mean()),
                            "ratio_std": max(float(ratio_series.std()), 1e-4)
                        }

    def verify_sensor(self,
                       sensor_id: str,
                       current_readings: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluates whether sensor_id's current reading is physically consistent
        with its topologically coupled neighbor sensors.
        """
        if sensor_id not in self.topology or sensor_id not in current_readings:
            return {
                "sensor_id": sensor_id,
                "is_consistent": True,
                "inconsistency_score": 0.0,
                "discrepancies": [],
                "coupled_peers_checked": []
            }

        target_val = current_readings[sensor_id]
        coupled_peers = self.topology[sensor_id]
        discrepancies = []
        peer_checks = []
        total_penalty = 0.0

        for peer in coupled_peers:
            if peer not in current_readings:
                continue
            peer_val = current_readings[peer]
            expected_corr = self.learned_correlations.get(sensor_id, {}).get(peer, 0.0)
            
            # Check ratio consistency if pair was learned
            ratio_key = (sensor_id, peer)
            if ratio_key in self.learned_ratios:
                r_stats = self.learned_ratios[ratio_key]
                current_ratio = target_val / (peer_val + 1e-4)
                z_ratio = abs(current_ratio - r_stats["ratio_mean"]) / r_stats["ratio_std"]
                
                # If strong correlation existed (|corr| > 0.4) and ratio deviated by > 3.5 z-scores
                if abs(expected_corr) > 0.4 and z_ratio > 3.5:
                    penalty = min(30.0, z_ratio * 4.0)
                    total_penalty += penalty
                    discrepancies.append(
                        f"Inconsistent with peer '{peer}': expected correlation {expected_corr:+.2f}, "
                        f"ratio deviated by {z_ratio:.1f}σ (observed: {target_val:.1f} vs peer: {peer_val:.1f})"
                    )

            peer_checks.append({
                "peer_id": peer,
                "peer_val": peer_val,
                "expected_correlation": expected_corr
            })

        # Check pump-tank physical rule:
        # If pump is operating at high flow (e.g. PU1 > 50 L/s), downstream pressure / tank level should not suddenly collapse
        if sensor_id.startswith("L_T") and target_val < 0.5:
            # Check if any associated pumps are running
            for p in coupled_peers:
                if p.startswith("F_PU") and current_readings.get(p, 0.0) > 30.0:
                    discrepancies.append(
                        f"Physical violation: Tank level near zero ({target_val:.2f}m) while feeding pump {p} is delivering high flow ({current_readings[p]:.1f} L/s)"
                    )
                    total_penalty += 35.0

        is_consistent = len(discrepancies) == 0
        normalized_inconsistency = min(1.0, total_penalty / 100.0)

        return {
            "sensor_id": sensor_id,
            "is_consistent": is_consistent,
            "inconsistency_score": round(normalized_inconsistency, 3),
            "discrepancies": discrepancies,
            "coupled_peers_checked": peer_checks
        }
