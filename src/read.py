from typing import List
import pandas as pd
import os
import yaml


def read_open_csv_files(path: str, csv_file: str):
    """Read CSV files for the OPEN original case"""
    csv_file_path = os.path.join(path, csv_file)
    return pd.read_csv(csv_file_path, index_col=0, parse_dates=True).values


def read_case_data_from_yaml_file(file_path: str, file_name: str):
    with open(os.path.join(file_path, file_name)) as file:
        case = yaml.safe_load(file)
    return case


def get_import_periods_from_yaml(file_path: str, file_name: str) -> List[dict]:
    case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=file_name)
    return case_data['import_periods']

