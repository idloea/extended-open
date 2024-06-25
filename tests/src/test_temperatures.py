import unittest
from src.temperatures import check_initial_inside_degree_celsius


class Temperatures(unittest.TestCase):

    def test_check_initial_inside_degree_celsius(self):
        max_inside_degree_celsius = 25
        min_inside_degree_celsius = 21
        initial_inside_degree_celsius = 21
        result = check_initial_inside_degree_celsius(initial_inside_degree_celsius=initial_inside_degree_celsius,
                                                     max_inside_degree_celsius=max_inside_degree_celsius,
                                                     min_inside_degree_celsius=min_inside_degree_celsius)
        expected_result = True
        self.assertEqual(expected_result, result)

