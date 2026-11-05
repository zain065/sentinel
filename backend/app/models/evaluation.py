"""
SENTINEL AI - Model Evaluation & Benchmarking
Calculates measurable performance metrics (Precision, Recall, F1, FPR, Confusion Matrix, Latency).
"""
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score


class ModelEvaluator:
    """Evaluates anomaly detection engines against ground-truth attack labels."""

    @staticmethod
    def calculate_metrics(y_true: np.ndarray,
                          y_pred: np.ndarray,
                          model_name: str = "Model",
                          attack_intervals: Optional[List[Tuple[int, int]]] = None) -> Dict[str, Any]:
        """
        Calculates standard classification metrics and detection latency.
        y_true: 1 for attack, 0 for normal
        y_pred: 1 for detected anomaly/attack, 0 for normal
        """
        y_true = np.asarray(y_true, dtype=int)
        y_pred = np.asarray(y_pred, dtype=int)

        if len(y_true) != len(y_pred):
            raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

        # Confusion Matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        
        acc = float(accuracy_score(y_true, y_pred))
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

        # Detection Latency per attack window
        latencies = []
        if attack_intervals is None:
            # Infer contiguous attack windows from y_true
            attack_intervals = []
            in_attack = False
            start = 0
            for idx, val in enumerate(y_true):
                if val == 1 and not in_attack:
                    in_attack = True
                    start = idx
                elif val == 0 and in_attack:
                    in_attack = False
                    attack_intervals.append((start, idx - 1))
            if in_attack:
                attack_intervals.append((start, len(y_true) - 1))

        for (start_idx, end_idx) in attack_intervals:
            window_preds = y_pred[start_idx: end_idx + 1]
            detected_indices = np.where(window_preds == 1)[0]
            if len(detected_indices) > 0:
                first_detection = int(detected_indices[0])  # Step offset from attack start
                latencies.append(first_detection)

        mean_latency = float(np.mean(latencies)) if latencies else None
        median_latency = float(np.median(latencies)) if latencies else None

        return {
            "model_name": model_name,
            "total_samples": int(len(y_true)),
            "attack_samples": int(np.sum(y_true)),
            "normal_samples": int(len(y_true) - np.sum(y_true)),
            "metrics": {
                "accuracy": round(acc, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "false_positive_rate": round(fpr, 4),
            },
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            },
            "latency": {
                "total_attacks": len(attack_intervals),
                "detected_attacks": len(latencies),
                "detection_rate": round(len(latencies) / len(attack_intervals), 4) if attack_intervals else 0.0,
                "mean_latency_steps": round(mean_latency, 2) if mean_latency is not None else None,
                "median_latency_steps": round(median_latency, 2) if median_latency is not None else None,
                "individual_latencies": latencies
            }
        }

