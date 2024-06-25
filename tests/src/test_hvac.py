import unittest
from src.hvac import get_hvac_consumed_electric_active_power_in_kilowatts


class TestHVAC(unittest.TestCase):

    def test_get_hvac_consumed_electric_active_power_in_kilowatts_heating(self):
        max_consumed_electric_heating_kilowatts = 50
        max_consumed_electric_cooling_kilowatts = None
        result = get_hvac_consumed_electric_active_power_in_kilowatts(max_consumed_electric_heating_kilowatts=
                                                                      max_consumed_electric_heating_kilowatts,
                                                                      max_consumed_electric_cooling_kilowatts=
                                                                      max_consumed_electric_cooling_kilowatts)

        expected_result = {'HVAC_heating': 50}
        self.assertEqual(expected_result, result)

    def test_get_hvac_consumed_electric_active_power_in_kilowatts_cooling(self):
        max_consumed_electric_heating_kilowatts = None
        max_consumed_electric_cooling_kilowatts = 50
        result = get_hvac_consumed_electric_active_power_in_kilowatts(max_consumed_electric_heating_kilowatts=
                                                                      max_consumed_electric_heating_kilowatts,
                                                                      max_consumed_electric_cooling_kilowatts=
                                                                      max_consumed_electric_cooling_kilowatts)

        expected_result = {'HVAC_cooling': 50}
        self.assertEqual(expected_result, result)

    def test_get_hvac_consumed_electric_active_power_in_kilowatts_cooling_too_many_inputs(self):
        max_consumed_electric_heating_kilowatts = 50
        max_consumed_electric_cooling_kilowatts = 50
        with self.assertRaises(ValueError):
            get_hvac_consumed_electric_active_power_in_kilowatts(max_consumed_electric_heating_kilowatts=
                                                                 max_consumed_electric_heating_kilowatts,
                                                                 max_consumed_electric_cooling_kilowatts=
                                                                 max_consumed_electric_cooling_kilowatts)

    def test_get_hvac_consumed_electric_active_power_in_kilowatts_cooling_empty_inputs(self):
        max_consumed_electric_heating_kilowatts = None
        max_consumed_electric_cooling_kilowatts = None
        with self.assertRaises(ValueError):
            get_hvac_consumed_electric_active_power_in_kilowatts(max_consumed_electric_heating_kilowatts=
                                                                 max_consumed_electric_heating_kilowatts,
                                                                 max_consumed_electric_cooling_kilowatts=
                                                                 max_consumed_electric_cooling_kilowatts)
