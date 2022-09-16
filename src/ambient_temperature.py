from abc import abstractmethod, ABC
from typing import Optional
import numpy as np
from scipy import signal
from src.read import read_meteo_navarra_ambient_temperature_csv_data


class DataStrategy(ABC):
    @abstractmethod
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[
                                                      float] = None, file_path: Optional[str] = None) -> np.array:
        pass


class UKData(DataStrategy):
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[
                                                      float] = None, file_path: Optional[str] = None) -> np.array:
        return predefined_ambient_temperature_in_degree_celsius * \
               np.ones(number_of_energy_management_time_intervals_per_day)


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
