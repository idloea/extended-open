import unittest
import numpy as np
from src.read import read_open_csv_files


class Read(unittest.TestCase):

    @staticmethod
    def test_read_open_csv_files():
        expected_result = [0.66400, 0.24700, 0.04800]

        path = 'tests/src/read'
        data = read_open_csv_files(path=path, csv_file='Loads_1min_2013JUN.csv')
        result = data[0][0:3]  # Get a sample
        np.testing.assert_almost_equal(expected_result, result)
