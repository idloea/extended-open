import unittest
import numpy as np
from src.interpolation import get_extrapolated_array_from_hour_to_minutes


class TestInterpolation(unittest.TestCase):

    def test_get_extrapolated_array_from_hour_to_minutes(self) -> None:
        array_in_hours = np.array([60, 120])
        result = get_extrapolated_array_from_hour_to_minutes(array_in_hours=array_in_hours)
        expected_result = np.array([np.ones(60), np.ones(60) * 2]).flatten()
        np.testing.assert_array_equal(expected_result, result)

