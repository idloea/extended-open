import datetime
import os
from abc import abstractmethod, ABC
from typing import Optional
import numpy as np
import pandas as pd
from scipy import signal
from scipy.interpolate import interpolate

from src.interpolation import get_extrapolated_array_from_hour_to_minutes
from src.read import read_preprocessing_meteo_navarra_ambient_temperature_csv_data, \
    read_meteo_navarra_ambient_temperature_csv_data


class DataStrategy(ABC):
    @abstractmethod
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[
                                                      float] = None, file_path: Optional[str] = None) -> np.array:
        pass

    @abstractmethod
    def get_building_electric_loads_per_minute(self, file_path: str, month: int) -> np.ndarray:
        pass


class UKData(DataStrategy):
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[
                                                      float] = None, file_path: Optional[str] = None) -> np.array:
        return predefined_ambient_temperature_in_degree_celsius * \
               np.ones(number_of_energy_management_time_intervals_per_day)

    def get_building_electric_loads_per_minute(self, file_path: str, month: int = None) -> np.ndarray:
        electric_loads = pd.read_csv(file_path, index_col=0, parse_dates=True).values
        return np.sum(electric_loads, 1)


class MeteoNavarraData(DataStrategy):
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[
                                                      float] = None, file_path: Optional[str] = None) -> np.array:
        data = read_meteo_navarra_ambient_temperature_csv_data(file_path=file_path)
        ambient_temperature_in_degree_celsius = data['DegreeCelsius']
        resampled_ambient_temperature_in_degree_celsius = \
            signal.resample(x=ambient_temperature_in_degree_celsius,
                            num=number_of_energy_management_time_intervals_per_day)
        return resampled_ambient_temperature_in_degree_celsius

    def get_building_electric_loads_per_minute(self, file_path: str, month: int) -> np.ndarray:
        df = pd.read_csv(file_path)
        df.rename(columns={"Power [kW]": "ActivePower_kW"}, inplace=True)
        df['YearlyHour'] = df.index
        start_date = pd.Timestamp('2020-01-01')  # 2020 has been randomly chosen since the year is not important
        yearly_hours = pd.to_timedelta(df['YearlyHour'], unit='H')
        df['DateTime'] = start_date + yearly_hours
        df['Date'] = df['DateTime'].dt.date
        year = 2020  # By default, since randomly 2020 has been chosen. The year is not important
        day = 15  # By default, select the 15th of the month
        specific_day = datetime.date(year, month, day)
        specific_day_df = df[df['Date'] == specific_day]
        active_power_in_kilowatts_per_hour = np.array(specific_day_df['ActivePower_kW'])
        return get_extrapolated_array_from_hour_to_minutes(array_in_hours=active_power_in_kilowatts_per_hour)


def get_ambient_temperature_in_degree_celsius_by_data_strategy(
        case_data: dict, number_of_energy_management_time_intervals_per_day: int) -> np.ndarray:
    data_strategy = case_data["data_strategy"]
    if data_strategy == 'UK':
        data = UKData()
        ambient_temperature_in_degree_celsius = case_data["ambient_temperature_in_degree_celsius"]
        ambient_temperature_in_degree_celsius = data.get_ambient_temperature_in_degree_celsius(
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day,
            predefined_ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius)
    elif data_strategy == 'MeteoNavarra':
        data = MeteoNavarraData()
        ambient_temperature_file_path = case_data["ambient_temperature_file_path"]
        ambient_temperature_in_degree_celsius = data.get_ambient_temperature_in_degree_celsius(
            number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day,
            file_path=ambient_temperature_file_path)
    else:
        raise ValueError(f'Incorrect data_strategy input. {data_strategy} is not available. ')

    return ambient_temperature_in_degree_celsius


def get_building_electric_loads_by_data_strategy(case_data: dict) -> np.ndarray:
    data_strategy = case_data["data_strategy"]
    if data_strategy == 'UK':
        data = UKData()
        file_path = case_data["electric_load_data_file"]
        building_electric_loads = data.get_building_electric_loads_per_minute(file_path=file_path)

    elif data_strategy == 'MeteoNavarra':
        data = MeteoNavarraData()
        file_path = case_data["electric_load_data_file"]
        month = case_data["month"]
        building_electric_loads = data.get_building_electric_loads_per_minute(file_path=file_path, month=month)
    else:
        raise ValueError(f'Incorrect data_strategy input. {data_strategy} is not available. ')

    return building_electric_loads
