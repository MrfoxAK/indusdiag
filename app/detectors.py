import pandas as pd


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


def detect_drift(df, window=5):

    findings = []

    values = df["value"]

    rolling_mean = values.rolling(window).mean()

    for i in range(window, len(values)):

        if rolling_mean[i] > rolling_mean[i-window] * 1.2:

            findings.append({
                "issue_type": "drift",
                "index": i,
                "value": values[i],
                "message": "Gradual upward drift detected"
            })

    return findings


def run_all_detectors(df):

    results = []

    results += detect_spike(df)
    results += detect_flatline(df)
    results += detect_missing_data(df)
    results += detect_out_of_range(df)
    results += detect_drift(df)

    return results