import pandas as pd
import os


def read_open_csv_files(path: str, csv_file: str):
    """Read CSV files for the OPEN original case"""
    csv_file_path = os.path.join(path, csv_file)
    return pd.read_csv(csv_file_path, index_col=0, parse_dates=True).values
