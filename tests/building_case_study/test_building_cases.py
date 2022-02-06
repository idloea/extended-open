import numpy as np
import unittest

from tests.building_case_study.summer_building_case_study import get_summer_building_case_original_results
from tests.building_case_study.winter_building_case_study import get_winter_building_case_original_results


class OriginalOPENTestBuildingCases(unittest.TestCase):

    def test_summer_building_case(self):
        # Results manually obtained from the original OPEN code for summer
        expected_revenue = 42.695890104240384
        expected_buses_Vpu = np.array([1., 0.9989054, 0.98702643])
        expected_buses_Vang = np.array([0., -0.25267629, -0.34076847])
        expected_buses_Pnet = np.array([-30.95076428, 0., 29.21800001])
        expected_buses_Qnet = np.array([-0.17804977, 0., 0.])
        expected_Pnet_market = 30.950764278638996
        expected_Qnet_market = 0.17804976753369842
        expected_P_import_ems = 25.9338000080222
        expected_P_export_ems = 2.3432962536501007e-09
        expected_P_BLDG_ems = 5.6789084149259585e-09
        expected_P_demand_ems = 25.933799999999998
        expected_P_demand_base = 29.218000000000004

        revenue, buses_Vpu, buses_Vang, buses_Pnet, buses_Qnet, Pnet_market, Qnet_market, buses_Vpu, P_import_ems, P_export_ems, P_BLDG_ems, P_demand_ems, P_demand_base = get_summer_building_case_original_results()

        np.testing.assert_almost_equal(expected_buses_Vpu, buses_Vpu)
        np.testing.assert_almost_equal(expected_buses_Vang, buses_Vang)
        np.testing.assert_almost_equal(expected_buses_Pnet, buses_Pnet)
        np.testing.assert_almost_equal(expected_buses_Qnet, buses_Qnet)
        self.assertAlmostEqual(expected_Pnet_market, Pnet_market)
        self.assertAlmostEqual(expected_Qnet_market, Qnet_market)
        self.assertAlmostEqual(expected_P_import_ems, P_import_ems)
        self.assertAlmostEqual(expected_P_export_ems, P_export_ems)
        self.assertAlmostEqual(expected_P_BLDG_ems, P_BLDG_ems)
        self.assertAlmostEqual(expected_P_demand_ems, P_demand_ems)
        self.assertAlmostEqual(expected_P_demand_base, expected_P_demand_base)
        self.assertAlmostEqual(expected_revenue, revenue)

    def test_winter_building_case(self):
        # Results manually obtained from the original OPEN code for summer
        expected_revenue = 90.48279419097048
        expected_buses_Vpu = np.array([1., 0.99518916, 0.94452166])
        expected_buses_Vang = np.array([0., - 1.05772496, - 1.43470765])
        expected_buses_Pnet = np.array([-127.52757771, 0., 119.21799983])
        expected_buses_Qnet = np.array([-3.17172107, 0., 0.])
        expected_Pnet_market = 127.52757771149913
        expected_Qnet_market = 3.171721069281089
        expected_P_import_ems = 115.93379983461517
        expected_P_export_ems = 6.473029541718239e-09
        expected_P_BLDG_ems = 89.99999982814215
        expected_P_demand_ems = 25.933799999999998
        expected_P_demand_base = 29.218000000000004

        revenue, buses_Vpu, buses_Vang, buses_Pnet, buses_Qnet, Pnet_market, Qnet_market, buses_Vpu, P_import_ems, P_export_ems, P_BLDG_ems, P_demand_ems, P_demand_base = get_winter_building_case_original_results()

        np.testing.assert_almost_equal(expected_buses_Vpu, buses_Vpu)
        np.testing.assert_almost_equal(expected_buses_Vang, buses_Vang)
        np.testing.assert_almost_equal(expected_buses_Pnet, buses_Pnet)
        np.testing.assert_almost_equal(expected_buses_Qnet, buses_Qnet)
        self.assertAlmostEqual(expected_Pnet_market, Pnet_market)
        self.assertAlmostEqual(expected_Qnet_market, Qnet_market)
        self.assertAlmostEqual(expected_P_import_ems, P_import_ems)
        self.assertAlmostEqual(expected_P_export_ems, P_export_ems)
        self.assertAlmostEqual(expected_P_BLDG_ems, P_BLDG_ems)
        self.assertAlmostEqual(expected_P_demand_ems, P_demand_ems)
        self.assertAlmostEqual(expected_P_demand_base, expected_P_demand_base)
        self.assertAlmostEqual(expected_revenue, revenue)
