"""
SENTINEL AI - BATADAL Model Training & Evaluation Pipeline
Trains Isolation Forest on official Dataset 03 (normal baseline),
evaluates against labeled Dataset 04 attack scenarios, and saves benchmarks.
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path("backend").resolve()))

from app.config import settings
from app.data.batadal_loader import BatadalLoader
from app.data.preprocessing import PreprocessingPipeline
from app.models.isolation_forest import IsolationForestDetector
from app.models.statistical_detector import StatisticalDetector
from app.detection.consistency import ConsistencyVerifier
from app.models.evaluation import ModelEvaluator


def run_pipeline():
    print("=" * 70)
    print("SENTINEL AI: OFFICIAL BATADAL MODEL TRAINING & EVALUATION")
    print("=" * 70)

    loader = BatadalLoader()
    status = loader.get_dataset_status()
    print("\n1. DATASET STATUS:")
    print(f"   Ready for training: {status['ready_for_training']}")
    for k, v in status["files"].items():
        print(f"   - {k}: {v['filename']} ({v['size_mb']} MB, exists={v['exists']})")

    if not status["ready_for_training"]:
        print("[ERROR] Required dataset files missing.")
        return

    # A. Load Dataset 03 (Normal Baseline)
    print("\n2. LOADING TRAINING DATASET 1 (Normal Baseline, 1 Year SCADA)...")
    df_train = loader.load_training_dataset_1()
    print(f"   Shape: {df_train.shape[0]} rows x {df_train.shape[1]} columns")
    print(f"   Date range: {df_train['DATETIME'].min()} to {df_train['DATETIME'].max()}")

    # B. Preprocessing & Scaling
    print("\n3. FITTING PREPROCESSING PIPELINE (Leakage-Free)...")
    pipeline = PreprocessingPipeline(scaler_type="standard")
    pipeline.fit(df_train)
    X_train_scaled = pipeline.transform(df_train)
    pipeline_path = pipeline.save()
    print(f"   Feature count: {len(pipeline.feature_columns)}")
    print(f"   Pipeline saved to: {pipeline_path}")

    # C. Fit Consistency Verifier Baseline
    print("\n4. LEARNING EPANET TOPOLOGICAL CROSS-SENSOR CORRELATIONS...")
    verifier = ConsistencyVerifier()
    verifier.fit_baseline_relationships(df_train)
    print(f"   Learned correlations for {len(verifier.learned_correlations)} coupled sensor clusters.")

    # D. Train Isolation Forest Model
    print("\n5. TRAINING UNSUPERVISED ISOLATION FOREST...")
    iforest = IsolationForestDetector(
        contamination=0.03,
        n_estimators=150,
        random_state=42
    )
    iforest.fit(X_train_scaled, pipeline.feature_columns)
    model_path = iforest.save()
    print(f"   Model fitted and serialized to: {model_path}")

    # E. Load Dataset 04 (Labeled Attacks)
    print("\n6. LOADING TRAINING DATASET 2 (Attack Scenarios with ATT_FLAG)...")
    df_eval = loader.load_training_dataset_2()
    print(f"   Shape: {df_eval.shape[0]} rows x {df_eval.shape[1]} columns")
    
    y_true = df_eval["ATT_FLAG"].values
    attack_count = int(np.sum(y_true))
    normal_count = int(len(y_true) - attack_count)
    print(f"   Attack points: {attack_count} ({round(attack_count/len(y_true)*100, 2)}%)")
    print(f"   Normal points: {normal_count} ({round(normal_count/len(y_true)*100, 2)}%)")

    # F. Run Model Inference
    print("\n7. RUNNING DETECTION INFERENCE ON ATTACK SCENARIOS...")
    X_eval_scaled = pipeline.transform(df_eval)
    raw_preds = iforest.predict(X_eval_scaled)
    # Convert sklearn (-1 anomaly, 1 normal) to (1 anomaly, 0 normal)
    y_pred_iforest = np.where(raw_preds == -1, 1, 0)
    anomaly_scores = iforest.anomaly_scores(X_eval_scaled)

    # Statistical baseline predictions
    stat_detector = StatisticalDetector()
    y_pred_stats = []
    for idx in range(len(df_eval)):
        sub_df = df_eval.iloc[max(0, idx - 12): idx + 1]
        # Check primary tank L_T1
        flag = stat_detector.analyze_sensor("L_T1", sub_df["L_T1"])["is_anomalous"]
        y_pred_stats.append(1 if flag else 0)
    y_pred_stats = np.array(y_pred_stats)

    # G. Calculate Evaluation Metrics
    print("\n8. COMPUTING QUANTITATIVE BENCHMARK METRICS...")
    report_iforest = ModelEvaluator.calculate_metrics(
        y_true, y_pred_iforest, model_name="Isolation Forest (Unsupervised)"
    )
    report_stats = ModelEvaluator.calculate_metrics(
        y_true, y_pred_stats, model_name="Statistical Baseline (Z-Score + Flatline)"
    )

    print("\n" + "=" * 50)
    print(f"MODEL BENCHMARK RESULTS: {report_iforest['model_name']}")
    print("=" * 50)
    m = report_iforest["metrics"]
    cm = report_iforest["confusion_matrix"]
    lat = report_iforest["latency"]

    print(f"Accuracy:              {m['accuracy'] * 100:.2f}%")
    print(f"Precision:             {m['precision'] * 100:.2f}%")
    print(f"Recall (Detection):    {m['recall'] * 100:.2f}%")
    print(f"F1-Score:              {m['f1_score']:.4f}")
    print(f"False Positive Rate:   {m['false_positive_rate'] * 100:.2f}%")
    print(f"\nConfusion Matrix:")
    print(f"  True Negatives:      {cm['true_negatives']}")
    print(f"  False Positives:     {cm['false_positives']}")
    print(f"  False Negatives:     {cm['false_negatives']}")
    print(f"  True Positives:      {cm['true_positives']}")
    print(f"\nAttack Scenario Latency:")
    print(f"  Total Attacks:       {lat['total_attacks']}")
    print(f"  Detected Attacks:    {lat['detected_attacks']} ({lat['detection_rate']*100:.1f}%)")
    print(f"  Mean Latency:        {lat['mean_latency_steps']} hours")
    print(f"  Median Latency:      {lat['median_latency_steps']} hours")

    # Save benchmark report to disk
    out_dir = Path("evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_file = out_dir / "batadal_benchmark_report.json"
    with open(report_file, "w") as f:
        json.dump({
            "dataset": "BATADAL (C-Town Water Distribution SCADA)",
            "training_dataset_1_samples": int(len(df_train)),
            "evaluation_dataset_2_samples": int(len(df_eval)),
            "models": {
                "isolation_forest": report_iforest,
                "statistical_baseline": report_stats
            }
        }, f, indent=2)

    print(f"\n[COMPLETED] Full benchmark report saved to: {report_file}")


if __name__ == "__main__":
    run_pipeline()
