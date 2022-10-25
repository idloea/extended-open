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


def read_preprocessing_meteo_navarra_ambient_temperature_csv_data(file_path: str) -> pd.DataFrame:
    """Read 10 min data from Meteo Navarra (http://meteo.navarra.es/estaciones/estacion.cfm?IDEstacion=405)"""
    data = pd.read_csv(file_path)
    data = data.iloc[:, 0:2]
    data.dropna(inplace=True)
    data.columns = ['DateTime', 'DegreeCelsius']
    data['Date'] = data.apply(lambda row: row['DateTime'][:10], axis=1)
    data['Time'] = data.apply(lambda row: row['DateTime'][10:], axis=1)
    data['DateTime'] = data['Date'] + '-' + data['Time']
    data['DateTime'] = pd.to_datetime(data['DateTime'], format='%d/%m/%Y-%H:%M')
    data['DegreeCelsius'] = pd.to_numeric(data['DegreeCelsius'], errors='coerce')
    data.reset_index(inplace=True)
    return data[['DateTime', 'DegreeCelsius']]


def read_meteo_navarra_ambient_temperature_csv_data(file_path: str) -> pd.DataFrame:
    """Read 10 min data from Meteo Navarra (http://meteo.navarra.es/estaciones/estacion.cfm?IDEstacion=405)"""
    data = pd.read_csv(file_path)
    data = data.iloc[:, 0:2]
    data.dropna(inplace=True)
    data.columns = ['DateTime', 'DegreeCelsius']
    data['Date'] = [row['DateTime'][:10] for row_index, row in data.iterrows()]
    data['Time'] = [row['DateTime'][10:] for row_index, row in data.iterrows()]
    data['DateTime'] = data['Date'] + '-' + data['Time']
    data['DateTime'] = pd.to_datetime(data['DateTime'])
    data['DegreeCelsius'] = pd.to_numeric(data['DegreeCelsius'], errors='coerce')
    data.reset_index(inplace=True)
    return data[['DateTime', 'DegreeCelsius']]


def get_import_period_prices_from_yaml(case_data: dict) -> List[dict]:
    return case_data['import_period_prices']


def get_specific_import_price(import_period_prices: dict, import_period: str) -> float:
    return import_period_prices[import_period]
