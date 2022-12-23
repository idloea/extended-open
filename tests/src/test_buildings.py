import unittest
from src.buildings import Hospital, Hotel, Office


class TestBuildings(unittest.TestCase):

    def test_hospital(self) -> None:
        building = Hospital()
        result = building.hvac_percentage_of_electric_load
        expected_result = 0.4
        self.assertEqual(expected_result, result)

    def test_hotel(self) -> None:
        building = Hotel()
        result = building.hvac_percentage_of_electric_load
        expected_result = 0.4
        self.assertEqual(expected_result, result)

    def test_office(self) -> None:
        building = Office()
        result = building.hvac_percentage_of_electric_load
        expected_result = 0.6
        self.assertEqual(expected_result, result)

