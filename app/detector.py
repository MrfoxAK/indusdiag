import pandas as pd

import numpy as np


def detect_spike(df, threshold=50):
    findings = []

    values = df["value"].values

    for i in range(1, len(values)-1):

        prev_val = values[i-1]
        curr_val = values[i]
        next_val = values[i+1]

        if abs(curr_val - prev_val) > threshold and abs(next_val - prev_val) < threshold:

            findings.append({
                "issue_type": "sensor_spike",
                "index": i,
                "value": curr_val,
                "message": f"Sudden spike detected: {prev_val} -> {curr_val}"
            })

    return findings


def detect_flatline(df, window=5):
    findings = []

    values = df["value"].values

    for i in range(len(values)-window):

        segment = values[i:i+window]

        if len(set(segment)) == 1:
            findings.append({
                "issue_type": "flatline",
                "index": i,
                "value": segment[0],
                "message": f"Flatline detected: value {segment[0]} repeated {window} times"
            })

    return findings


def detect_missing_data(df, expected_interval_minutes=1):

    findings = []

    times = df["timestamp"]

    diffs = times.diff()

    for i, diff in enumerate(diffs):

        if pd.notnull(diff):

            minutes = diff.total_seconds() / 60

            if minutes > expected_interval_minutes * 2:

                findings.append({
                    "issue_type": "missing_data",
                    "index": i,
                    "message": f"Missing data gap detected: {minutes:.2f} minutes"
                })

    return findings


def detect_out_of_range(df, min_val=0, max_val=200):

    findings = []

    for i, row in df.iterrows():

        if row["value"] < min_val or row["value"] > max_val:

            findings.append({
                "issue_type": "out_of_range",
                "index": i,
                "value": row["value"],
                "message": f"Value {row['value']} outside range ({min_val}, {max_val})"
            })

    return findings


def detect_drift(df, window=5, threshold_pct=0.15):
    findings = []
    values = df["value"]
    rolling_mean = values.rolling(window).mean()

    for i in range(window, len(values)):
        prev = rolling_mean[i - window]
        curr = rolling_mean[i]
        if prev == 0:
            continue

        change_pct = (curr - prev) / abs(prev)

        # Catch BOTH upward and downward drift
        if change_pct > threshold_pct:
            findings.append({
                "issue_type": "drift",
                "index": i,
                "value": float(values[i]),
                "message": f"Gradual upward drift detected ({change_pct*100:.1f}% change)"
            })
        elif change_pct < -threshold_pct:
            findings.append({
                "issue_type": "drift",
                "index": i,
                "value": float(values[i]),
                "message": f"Gradual downward drift detected ({change_pct*100:.1f}% change)"
            })

    return findings


def detect_pump_cavitation(
    df: pd.DataFrame,
    window: int = 10,
    low_factor: float = 0.8,
    oscillations_threshold: int = 3,
    amplitude_min_pct: float = 0.05,
) -> list[dict]:
    """
    Heuristic pump cavitation detection.

    Cavitation commonly shows up as:
    - pressure (or proxy signal) dropping below a short-term baseline
    - oscillatory behavior (rapid sign flips in first differences)
    - enough amplitude to be distinguishable from noise

    This is a generic rule that operates on `df["value"]` and assumes
    the input series already corresponds to a cavitation-relevant tag.
    """
    findings: list[dict] = []

    if window < 3 or len(df) < window + 1:
        return findings

    values = df["value"]
    rolling_median = values.rolling(window=window, min_periods=window).median()

    # Check windows ending at index i
    for i in range(window, len(values)):
        baseline = rolling_median.iloc[i]
        if pd.isna(baseline) or baseline == 0:
            continue

        curr = float(values.iloc[i])
        # Cavitation proxy: current reading is sufficiently below baseline.
        if curr > float(baseline) * low_factor:
            continue

        start = i - window + 1
        segment = values.iloc[start : i + 1].astype(float).to_numpy()
        amplitude = float(np.max(segment) - np.min(segment))
        if amplitude < abs(float(baseline)) * amplitude_min_pct:
            continue

        diffs = np.diff(segment)
        if diffs.size < 2:
            continue

        signs = np.sign(diffs)
        # Count sign flips excluding zero/flat changes
        non_zero = (signs[:-1] != 0) & (signs[1:] != 0)
        sign_changes = int(np.sum((signs[:-1] * signs[1:] < 0) & non_zero))

        if sign_changes >= oscillations_threshold:
            findings.append(
                {
                    "issue_type": "pump_cavitation",
                    "index": i,
                    "value": curr,
                    "message": (
                        "Pump cavitation suspected: oscillatory drop below baseline "
                        f"(baseline≈{float(baseline):.2f}, curr={curr:.2f}, "
                        f"oscillations={sign_changes}, amplitude≈{amplitude:.2f})"
                    ),
                }
            )

    return findings


def run_all_detectors(df):

    results = []

    results += detect_spike(df)
    results += detect_flatline(df)
    results += detect_missing_data(df)
    results += detect_out_of_range(df)
    results += detect_drift(df)
    results += detect_pump_cavitation(df)

    return results