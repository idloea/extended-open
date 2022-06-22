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


def read_meteo_navarra_solar_radiation_data(file_path: str) -> pd.DataFrame:
    """Read 10 min data from Meteo Navarra (http://meteo.navarra.es/energiasrenovables/estacionradiacion.cfm)"""
    data = pd.read_excel(file_path, engine='openpyxl')
    data['Timestamp'] = pd.to_datetime(data['Timestamp'])
    data.sort_values(by=['Timestamp'], inplace=True)
    data['Date'] = data['Timestamp'].dt.to_period('D')
    data = data.set_index('Timestamp')
    return data
