import numpy as np
import unittest

from tests.building_case_study.building_case_study_for_tests import get_building_case_original_results


class OriginalOPENTestBuildingCases(unittest.TestCase):

    def test_summer_building_case(self):
        is_winter = False
        # Results manually obtained from the original OPEN code for summer
        expected_revenue = 42.695890104240384
        expected_buses_voltage_in_per_unit = np.array([1., 0.9989054, 0.98702643])
        expected_buses_buses_voltage_angle_in_degrees = np.array([0., -0.25267629, -0.34076847])
        expected_buses_active_power_in_kilowatts = np.array([-30.95076428, 0., 29.21800001])
        expected_buses_reactive_power_in_kilovolt_ampere_reactive = np.array([-0.17804977, 0., 0.])
        expected_market_active_power_in_kilowatts = 30.950764278638996
        expected_market_reactive_power_in_kilovolt_ampere_reactive = 0.17804976753369842
        expected_imported_active_power_in_kilowatts = 25.9338000080222
        expected_exported_active_power_in_kilowatts = 2.3432962536501007e-09
        expected_building_power_consumption_in_kilowatts = 5.6789084149259585e-09
        expected_active_power_demand_in_kilowatts = 25.933799999999998
        expected_active_power_demand_base_in_kilowatts = 29.218000000000004

        revenue, buses_voltage_in_per_unit, buses_voltage_angle_in_degrees, buses_active_power_in_kilowatts, \
        buses_reactive_power_in_kilovolt_ampere_reactive, market_active_power_in_kilowatts, \
        market_reactive_power_in_kilovolt_ampere_reactive, imported_active_power_in_kilowatts, \
        exported_active_power_in_kilowatts, building_power_consumption_in_kilowatts, active_power_demand_in_kilowatts, \
        active_power_demand_base_in_kilowatts = get_building_case_original_results(is_winter=is_winter)

        np.testing.assert_almost_equal(expected_buses_voltage_in_per_unit, buses_voltage_in_per_unit)
        np.testing.assert_almost_equal(expected_buses_buses_voltage_angle_in_degrees, buses_voltage_angle_in_degrees)
        np.testing.assert_almost_equal(expected_buses_active_power_in_kilowatts, buses_active_power_in_kilowatts,
                                       decimal=4)
        np.testing.assert_almost_equal(expected_buses_reactive_power_in_kilovolt_ampere_reactive,
                                       buses_reactive_power_in_kilovolt_ampere_reactive)
        self.assertAlmostEqual(expected_market_active_power_in_kilowatts, market_active_power_in_kilowatts, places=4)
        self.assertAlmostEqual(expected_market_reactive_power_in_kilovolt_ampere_reactive,
                               market_reactive_power_in_kilovolt_ampere_reactive)
        self.assertAlmostEqual(expected_imported_active_power_in_kilowatts, imported_active_power_in_kilowatts,
                               places=4)
        self.assertAlmostEqual(expected_exported_active_power_in_kilowatts, exported_active_power_in_kilowatts,
                               places=4)
        self.assertAlmostEqual(expected_building_power_consumption_in_kilowatts,
                               building_power_consumption_in_kilowatts, places=4)
        self.assertAlmostEqual(expected_active_power_demand_in_kilowatts, active_power_demand_in_kilowatts, places=4)
        self.assertAlmostEqual(expected_active_power_demand_base_in_kilowatts,
                               expected_active_power_demand_base_in_kilowatts, places=4)
        self.assertAlmostEqual(expected_revenue, revenue, places=4)

    def test_winter_building_case(self):
        is_winter = True
        # Results manually obtained from the original OPEN code for summer
        expected_revenue = 103.87032557045784
        expected_buses_Vpu = np.array([1., 0.99458841, 0.93796202])
        expected_buses_Vang = np.array([0., -1.18118568, -1.60273713])
        expected_buses_Pnet = np.array([-142.34896823, 0., 132.30699109])
        expected_buses_Qnet = np.array([-3.95819044, 0., 0.])
        expected_Pnet_market = 142.348968233712
        expected_Qnet_market = 3.958190435584834
        expected_P_import_ems = 127.23482471394126
        expected_P_export_ems = 2.8688983452894103e-07
        expected_P_BLDG_ems = 89.9999910937181
        expected_P_demand_ems = 37.23483333333333
        expected_P_demand_base = 42.30700000000001

        revenue, buses_Vpu, buses_Vang, buses_Pnet, buses_Qnet, Pnet_market, Qnet_market, P_import_ems, P_export_ems, P_BLDG_ems, P_demand_ems, P_demand_base = get_building_case_original_results(
            is_winter=is_winter)

        np.testing.assert_almost_equal(expected_buses_Vpu, buses_Vpu)
        np.testing.assert_almost_equal(expected_buses_Vang, buses_Vang)
        np.testing.assert_almost_equal(expected_buses_Pnet, buses_Pnet, decimal=4)
        np.testing.assert_almost_equal(expected_buses_Qnet, buses_Qnet, decimal=4)
        self.assertAlmostEqual(expected_Pnet_market, Pnet_market, places=4)
        self.assertAlmostEqual(expected_Qnet_market, Qnet_market, places=4)
        self.assertAlmostEqual(expected_P_import_ems, P_import_ems, places=4)
        self.assertAlmostEqual(expected_P_export_ems, P_export_ems, places=4)
        self.assertAlmostEqual(expected_P_BLDG_ems, P_BLDG_ems, places=4)
        self.assertAlmostEqual(expected_P_demand_ems, P_demand_ems, places=4)
        self.assertAlmostEqual(expected_P_demand_base, expected_P_demand_base, places=4)
        self.assertAlmostEqual(expected_revenue, revenue, places=4)
