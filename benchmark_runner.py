import os

from app.parser import parse_sensor_data
from app.anomaly_detector import detect_anomalies
from app.reasoner import generate_diagnostic_report
from app.claude_reasoner import claude_diagnose

BENCHMARK_DIR = "benchmarks"

EXPECTED_RESULTS = {
    "furnace_sensor_spike.csv": "spike",
    "conveyor_motor_overheat.csv": "overheat",
    "pressure_sensor_drift.csv": "drift",
    "vibration_bearing_failure.csv": "bearing",
    "flow_sensor_blockage.csv": "block"
}


def score_report(report, keyword):

    if keyword in report.lower():
        return 2000
    else:
        return 1000


def run_benchmark():

    indus_total = 0
    claude_total = 0

    print("\nRunning IndusDiag vs Claude Benchmarks\n")

    for file in os.listdir(BENCHMARK_DIR):

        if not file.endswith(".csv"):
            continue

        path = os.path.join(BENCHMARK_DIR, file)

        print("Dataset:", file)

        data = parse_sensor_data(path)

        findings = detect_anomalies(data)

        asset = data["asset"].iloc[0]

        print("Running IndusDiag reasoning...")
        indus_report = generate_diagnostic_report(findings, asset)

        print("Running Claude reasoning...")
        claude_report = claude_diagnose(findings, asset)

        expected = EXPECTED_RESULTS[file]

        indus_score = score_report(indus_report, expected)
        claude_score = score_report(claude_report, expected)

        indus_total += indus_score
        claude_total += claude_score

        print("\nIndusDiag Report\n")
        print(indus_report)

        print("\nClaude Report\n")
        print(claude_report)

        print("\nScores")
        print("IndusDiag:", indus_score)
        print("Claude:", claude_score)

        print("\n-------------------------------\n")

    print("\nFinal Results\n")

    print("IndusDiag Score:", indus_total, "/10000")
    print("Claude Score:", claude_total, "/10000")


if __name__ == "__main__":
    run_benchmark()