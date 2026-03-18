from rich import print

from app.parser import parse_sensor_data
from app.detectors import run_all_detectors
from app.reasoner import generate_diagnostic_report


def main():
    file_path = "data/samples/sensor_spike.csv"

    print("[bold blue]Loading sensor data...[/bold blue]")
    df = parse_sensor_data(file_path)
    print("[green]Data parsed successfully[/green]")

    findings = run_all_detectors(df)

    print("\n[bold yellow]Anomaly Findings[/bold yellow]\n")
    if not findings:
        print("[green]No anomalies detected[/green]")
        return

    for finding in findings:
        print(finding)

    print("\n[bold magenta]Generating AI diagnostic report...[/bold magenta]\n")

    report = generate_diagnostic_report(findings, asset_name="FurnaceSensorA")

    print("[bold green]AI Diagnostic Report[/bold green]\n")
    print(report)


if __name__ == "__main__":
    main()