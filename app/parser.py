import pandas as pd


REQUIRED_COLUMNS = [
    "timestamp",
    "tag",
    "value",
    "unit",
    "asset",
    "status"
]


def parse_sensor_data(file_path: str) -> pd.DataFrame:
    """
    Parse industrial sensor log CSV file and return normalized dataframe.
    """

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Error reading file: {e}")

    # Validate required columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Convert timestamp
    # Be tolerant: if the timestamp format is inconsistent, coerce invalid rows
    # to NaT and drop them instead of hard-failing the whole upload.
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])

    # Sort by time
    df = df.sort_values("timestamp")

    # Convert value to numeric
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # Drop invalid rows
    df = df.dropna(subset=["value"])

    return df