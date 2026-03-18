from rich import print
from app.parser import parse_sensor_data


def main():

    file_path = "data/samples/sensor_spike.csv"

    print("[bold blue]Loading sensor data...[/bold blue]")

    df = parse_sensor_data(file_path)

    print("[green]Data successfully parsed![/green]")

    print(df)


if __name__ == "__main__":
    main()