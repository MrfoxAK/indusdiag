def detect_anomalies(data):

    findings = []

    values = data["value"].tolist()

    for i in range(1, len(values)):
        if abs(values[i] - values[i-1]) > 100:
            findings.append({
                "issue_type": "sensor_spike",
                "index": i,
                "value": values[i],
                "message": f"Sudden spike detected: {values[i-1]} -> {values[i]}"
            })

    return findings


def detect_pump_cavitation(
    data,
    window: int = 10,
    low_factor: float = 0.8,
    oscillations_threshold: int = 3,
    amplitude_min_pct: float = 0.05,
):
    """
    Lightweight cavitation heuristic operating on `data["value"]`.

    This module is an older/alternate detector entrypoint; the main agent
    pipeline uses `app/detector.py` instead.
    """
    values = data["value"].tolist()
    if window < 3 or len(values) < window + 1:
        return []

    findings = []
    for i in range(window, len(values)):
        window_vals = values[i - window + 1 : i + 1]
        baseline = sorted(window_vals)[window // 2]
        if baseline == 0:
            continue

        curr = values[i]
        if curr > baseline * low_factor:
            continue

        amplitude = max(window_vals) - min(window_vals)
        if amplitude < abs(baseline) * amplitude_min_pct:
            continue

        diffs = [window_vals[j + 1] - window_vals[j] for j in range(len(window_vals) - 1)]
        sign_changes = 0
        prev_sign = 0
        for d in diffs:
            sign = 0
            if d > 0:
                sign = 1
            elif d < 0:
                sign = -1
            if sign != 0 and prev_sign != 0 and sign != prev_sign:
                sign_changes += 1
            if sign != 0:
                prev_sign = sign

        if sign_changes >= oscillations_threshold:
            findings.append(
                {
                    "issue_type": "pump_cavitation",
                    "index": i,
                    "value": curr,
                    "message": (
                        "Pump cavitation suspected: oscillatory drop below baseline "
                        f"(baseline≈{baseline:.2f}, curr={curr:.2f}, "
                        f"oscillations={sign_changes}, amplitude≈{amplitude:.2f})"
                    ),
                }
            )

    return findings