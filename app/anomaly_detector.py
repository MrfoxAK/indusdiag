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