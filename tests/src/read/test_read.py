import unittest
import numpy as np
from src.read import read_open_csv_files, get_import_periods_from_yaml


class Read(unittest.TestCase):

    @staticmethod
    def test_read_open_csv_files():
        expected_result = [0.66400, 0.24700, 0.04800]

        path = 'tests/src/read'
        data = read_open_csv_files(path=path, csv_file='Loads_1min_2013JUN.csv')
        result = data[0][0:3]  # Get a sample
        np.testing.assert_almost_equal(expected_result, result)

    def test_get_import_periods_from_yaml(self):
        file_name = 'case_for_testing.yaml'
        file_path = 'tests/src/read'
        result = get_import_periods_from_yaml(file_path=file_path, file_name=file_name)
        expected_result = [{'peak': [7, 0.083]}, {'valley': [17, 0.18]}]
        self.assertEqual(expected_result, result)

