from rich import print
from app.parser import parse_sensor_data
from app.detectors import run_all_detectors


def main():

    file_path = "data/samples/sensor_spike.csv"

    print("[bold blue]Loading sensor data...[/bold blue]")

    df = parse_sensor_data(file_path)

    print("[green]Data parsed successfully[/green]")

    findings = run_all_detectors(df)

    print("\n[bold yellow]Anomaly Findings[/bold yellow]\n")

    if not findings:
        print("[green]No anomalies detected[/green]")
    else:
        for f in findings:
            print(f)


if __name__ == "__main__":
    main()