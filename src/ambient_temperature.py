from abc import abstractmethod, ABC
from typing import Optional
import numpy as np
from scipy import signal
from skimage.measure import block_reduce
from src.read import read_meteo_navarra_ambient_temperature_csv_data


class DataStrategy(ABC):
    @abstractmethod
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_system_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[float] = None,
                                                  file_path: Optional[str] = None) -> np.array:
        pass


class UKData(DataStrategy):
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_system_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[float] = None,
                                                  file_path: Optional[str] = None) -> np.array:
        return predefined_ambient_temperature_in_degree_celsius * \
               np.ones(number_of_energy_management_system_time_intervals_per_day)


class MeteoNavarraData(DataStrategy):
    def get_ambient_temperature_in_degree_celsius(self, number_of_energy_management_time_intervals_per_day: int,
                                                  predefined_ambient_temperature_in_degree_celsius: Optional[float] = None,
                                                  file_path: Optional[str] = None) -> np.array:
        data = read_meteo_navarra_ambient_temperature_csv_data(file_path=file_path)
        ambient_temperature_in_degree_celsius = data['DegreeCelsius']
        resampled_ambient_temperature_in_degree_celsius = \
            signal.resample(x=ambient_temperature_in_degree_celsius,
                            num=number_of_energy_management_time_intervals_per_day)
        return resampled_ambient_temperature_in_degree_celsius
