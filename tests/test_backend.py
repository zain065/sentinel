"""
SENTINEL AI - Automated Backend Verification Suite
Tests data validation, statistical detector, consistency verifier,
trust engine, FDI attack simulator, and API route handlers directly.
"""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Ensure backend directory is in python path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.config import settings
from app.data.validation import DataValidator
from app.data.batadal_loader import BatadalLoader
from app.models.statistical_detector import StatisticalDetector
from app.models.isolation_forest import IsolationForestDetector
from app.detection.consistency import ConsistencyVerifier
from app.detection.attack_simulator import AttackSimulator
from app.trust.trust_engine import TrustEngine
from app.models.evaluation import ModelEvaluator
from app.api.routes import health_check, get_dataset_status, list_sensors, run_detection, simulate_attack, DetectionRequest, SimulationRequest


class TestSentinelBackend(unittest.TestCase):

    def test_health_route(self):
        """Verify health check endpoint returns online status."""
        data = health_check()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["app"], "SENTINEL AI")

    def test_dataset_status_route(self):
        """Verify dataset status endpoint accurately checks raw file presence without fabricating."""
        data = get_dataset_status()
        self.assertIn("ready_for_training", data)
        self.assertIn("files", data)
        # Verify files are properly identified
        self.assertIn("training_dataset_1", data["files"])

    def test_sensors_route(self):
        """Verify sensors listing returns all C-Town sensors with valid trust scores."""
        data = list_sensors()
        self.assertGreaterEqual(data["total_sensors"], 30)
        self.assertIn("sensors", data)
        first_sensor = data["sensors"][0]
        self.assertIn("sensor_id", first_sensor)
        self.assertTrue(0.0 <= first_sensor["trust_score"] <= 100.0)

    def test_statistical_flatline_detection(self):
        """Verify detector catches frozen constant-value sensor signals."""
        detector = StatisticalDetector(flatline_hours=4)
        frozen_series = pd.Series([10.2, 11.5, 12.0, 15.0, 15.0, 15.0, 15.0])
        self.assertTrue(detector.check_flatline(frozen_series))

        dynamic_series = pd.Series([10.2, 11.5, 12.0, 15.0, 15.2, 15.1, 15.4])
        self.assertFalse(detector.check_flatline(dynamic_series))

    def test_statistical_rate_of_change(self):
        """Verify detector catches unrealistic instantaneous step violations."""
        detector = StatisticalDetector()
        normal_series = pd.Series([5.0, 5.2, 5.3])
        self.assertFalse(detector.check_rate_of_change(normal_series, baseline_max_delta=0.5))

        spike_series = pd.Series([5.0, 5.2, 25.0])
        self.assertTrue(detector.check_rate_of_change(spike_series, baseline_max_delta=0.5))

    def test_attack_simulator_vectors(self):
        """Verify attack simulator injects attack types without altering original data."""
        df = pd.DataFrame({"L_T1": [5.0 + 0.1 * i for i in range(50)]})
        original_copy = df["L_T1"].values.copy()

        # 1. Value manipulation
        res = AttackSimulator.inject_attack(df, "L_T1", "value_manipulation", start_index=10, duration_steps=10, intensity=2.0)
        self.assertTrue(res["is_synthetic_simulation"])
        self.assertTrue(np.array_equal(df["L_T1"].values, original_copy))
        sim_series = res["simulated_dataframe"]["L_T1"].values
        self.assertFalse(np.array_equal(sim_series, original_copy))

        # 2. Constant value freeze
        res_freeze = AttackSimulator.inject_attack(df, "L_T1", "constant_value", start_index=15, duration_steps=10)
        frozen_segment = res_freeze["simulated_dataframe"]["L_T1"].iloc[15:25]
        self.assertEqual(frozen_segment.nunique(), 1)

    def test_trust_engine_scoring(self):
        """Verify trust engine dynamically deducts score on anomalies and recovers on normal steps."""
        engine = TrustEngine()
        s_id = "L_T1"
        
        # Initial score should be 100
        res_clean = engine.compute_trust_step(s_id)
        self.assertEqual(res_clean["trust_score"], 100.0)
        self.assertEqual(res_clean["status"], "Trusted")

        # Penalize with ML anomaly & rate violation
        res_anom = engine.compute_trust_step(s_id, ml_anomaly_score=0.9, rate_violation=True)
        self.assertLess(res_anom["trust_score"], 100.0)
        self.assertGreater(res_anom["total_penalty"], 0)
        self.assertGreater(len(res_anom["evidence"]), 0)

        # Step clean again -> recovery
        res_recover = engine.compute_trust_step(s_id)
        self.assertGreater(res_recover["trust_score"], res_anom["trust_score"])

    def test_simulation_route(self):
        """Verify simulation API route injects attack and returns benchmark latency."""
        req = SimulationRequest(
            sensor_id="L_T1",
            attack_type="value_manipulation",
            start_index=10,
            duration_steps=15,
            intensity=3.0
        )
        resp = simulate_attack(req)
        self.assertIn("simulation_parameters", resp)
        self.assertIn("detection_benchmark", resp)
        self.assertTrue(resp["detection_benchmark"]["was_detected"])
        self.assertIsNotNone(resp["detection_benchmark"]["detection_latency_steps"])

    def test_model_evaluation_metrics(self):
        """Verify evaluation metric computation against ground truth."""
        y_true = np.array([0, 0, 0, 1, 1, 1, 0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 1, 1, 0, 0, 0, 1, 1])
        
        report = ModelEvaluator.calculate_metrics(y_true, y_pred, model_name="TestDetector")
        metrics = report["metrics"]
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 0.8)
        self.assertEqual(report["latency"]["total_attacks"], 2)


if __name__ == "__main__":
    unittest.main()
