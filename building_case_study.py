import numpy as np

from src.read import read_open_csv_files


data_path = "Data/Building/"
photovoltaic_generation_data_file = "PVpu_1min_2014JAN.csv"
photovoltaic_generation_in_per_unit = read_open_csv_files(path=data_path,
                                                          csv_file=photovoltaic_generation_data_file)
electric_load_data_file = "Loads_1min_2014JAN.csv"
electric_loads = read_open_csv_files(path=data_path, csv_file=electric_load_data_file)

sum_of_photovoltaic_generation_in_per_unit = np.sum(photovoltaic_generation_in_per_unit, 1)

is_winter = True

photovoltaic_generation_per_unit = sum_of_photovoltaic_generation_in_per_unit / \
                                   np.max(sum_of_photovoltaic_generation_in_per_unit)

