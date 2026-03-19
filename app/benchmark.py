"""
benchmark.py
Evaluates the performance of IndusDiag detectors against labeled ground-truth data.

Usage:
    python -m app.benchmark --data data/samples/labeled_test.csv

The labeled CSV must have all standard columns plus a `label` column
with the expected issue_type (or "normal" for clean rows).
"""

import argparse
import json
from typing import Dict, List, Tuple

import pandas as pd

from app.parser import parse_sensor_data
from app.detector import run_all_detectors
from app.scorer import score_all_findings


# ---------------------------------------------------------------------------
# Ground truth extraction
# ---------------------------------------------------------------------------

def extract_ground_truth(df: pd.DataFrame) -> Dict[int, str]:
    """
    Extract the ground truth labels from the dataframe.
    Expects a `label` column with values like 'sensor_spike', 'flatline', 'normal'.
    Returns a dict of {row_index: label}.
    """
    if "label" not in df.columns:
        raise ValueError("Benchmark CSV must have a 'label' column.")

    return {
        int(i): str(row["label"])
        for i, row in df.iterrows()
        if row["label"] != "normal"
    }


# ---------------------------------------------------------------------------
# Precision / Recall / F1
# ---------------------------------------------------------------------------

def compute_metrics(
    predicted_indices: List[int],
    ground_truth: Dict[int, str],
    total_rows: int,
) -> Dict[str, float]:
    """
    Compute precision, recall, and F1 for anomaly detection.

    predicted_indices: list of row indices flagged by detectors
    ground_truth: dict of {index: issue_type} for truly anomalous rows
    total_rows: total number of rows in the dataset
    """
    true_positives = len(set(predicted_indices) & set(ground_truth.keys()))
    false_positives = len(set(predicted_indices) - set(ground_truth.keys()))
    false_negatives = len(set(ground_truth.keys()) - set(predicted_indices))

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
    }


# ---------------------------------------------------------------------------
# Per-detector breakdown
# ---------------------------------------------------------------------------

def benchmark_per_detector(
    df: pd.DataFrame,
    ground_truth: Dict[int, str],
) -> Dict[str, Dict]:
    """Run each detector individually and measure its metrics."""
    from app.detector import (
        detect_spike,
        detect_flatline,
        detect_missing_data,
        detect_out_of_range,
        detect_drift,
        detect_pump_cavitation,
    )

    detectors = {
        "spike": detect_spike,
        "flatline": detect_flatline,
        "missing_data": detect_missing_data,
        "out_of_range": detect_out_of_range,
        "drift": detect_drift,
        "pump_cavitation": detect_pump_cavitation,
    }

    results = {}
    for name, fn in detectors.items():
        try:
            findings = fn(df)
            predicted = [f["index"] for f in findings]
            # Filter ground truth to this detector's issue type
            relevant_gt = {
                i: t for i, t in ground_truth.items()
                if name in t  # e.g. "sensor_spike" contains "spike"
            }
            metrics = compute_metrics(predicted, relevant_gt, len(df))
            metrics["findings_count"] = len(findings)
            results[name] = metrics
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


# ---------------------------------------------------------------------------
# Full benchmark run
# ---------------------------------------------------------------------------

def run_benchmark(data_path: str, verbose: bool = True) -> Dict:
    """
    Full benchmark run on a labeled CSV file.
    Returns a dict with overall and per-detector metrics.
    """
    df = parse_sensor_data(data_path)
    ground_truth = extract_ground_truth(df)

    all_findings = run_all_detectors(df)
    scored_findings = score_all_findings(all_findings)
    predicted_indices = [f["index"] for f in all_findings]

    overall = compute_metrics(predicted_indices, ground_truth, len(df))
    per_detector = benchmark_per_detector(df, ground_truth)

    result = {
        "file": data_path,
        "total_rows": len(df),
        "anomalous_rows_in_ground_truth": len(ground_truth),
        "total_findings_detected": len(all_findings),
        "overall_metrics": overall,
        "per_detector": per_detector,
    }

    if verbose:
        print("\n" + "=" * 60)
        print("  BENCHMARK RESULTS")
        print("=" * 60)
        print(f"  File:          {data_path}")
        print(f"  Total rows:    {len(df)}")
        print(f"  Ground truth:  {len(ground_truth)} anomalous rows")
        print(f"  Detected:      {len(all_findings)} findings")
        print(f"\n  Overall Metrics:")
        for k, v in overall.items():
            print(f"    {k:<22} {v}")
        print(f"\n  Per-Detector Breakdown:")
        for det, metrics in per_detector.items():
            print(f"\n  [{det}]")
            for k, v in metrics.items():
                print(f"    {k:<22} {v}")
        print("=" * 60 + "\n")

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark IndusDiag detectors")
    parser.add_argument(
        "--data",
        default="data/samples/labeled_test.csv",
        help="Path to labeled CSV file",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save JSON results",
    )
    args = parser.parse_args()

    results = run_benchmark(args.data)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
