import unittest
import numpy as np
from src.ambient_temperature import UKData, MeteoNavarraData


class TestAmbientTemperature(unittest.TestCase):

    def test_UKData_get_ambient_temperature_in_degree_celsius(self):
        number_of_energy_management_system_time_intervals_per_day = 96
        ambient_temperature_in_degree_celsius = 20
        uk_data = UKData()
        result = uk_data.get_ambient_temperature_in_degree_celsius(
            number_of_energy_management_system_time_intervals_per_day=
            number_of_energy_management_system_time_intervals_per_day,
            predefined_ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius)
        expected_result = np.full(shape=96, fill_value=20)
        np.testing.assert_equal(expected_result, result)

    def test_MeteoNavarraData_get_ambient_temperature_in_degree_celsius(self):
        number_of_energy_management_system_time_intervals_per_day = 96
        file_path = 'tests/src/ambient_temperature/20220717_ambient_temperature_upna.csv'
        meteo_navarra_data = MeteoNavarraData()
        ambient_temperature_in_degree_celsius = meteo_navarra_data.get_ambient_temperature_in_degree_celsius(
            number_of_energy_management_time_intervals_per_day=
            number_of_energy_management_system_time_intervals_per_day,
            file_path=file_path)
        result = ambient_temperature_in_degree_celsius[0:5]
        expected_result = np.array([20.05045488, 20.15392266, 19.02882983, 18.43678492, 17.87204455])
        np.testing.assert_array_almost_equal(expected_result, result)
