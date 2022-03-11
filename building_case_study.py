import numpy as np
from src.electric_vehicles import ElectricVehicleFleet
from src.read import read_open_csv_files
import pandapower as pp

# STEP 0: Load Data
data_path = "Data/Building/"
photovoltaic_generation_data_file = "PVpu_1min_2014JAN.csv"
photovoltaic_generation_in_per_unit = read_open_csv_files(path=data_path,
                                                          csv_file=photovoltaic_generation_data_file)
electric_load_data_file = "Loads_1min_2014JAN.csv"
electric_loads = read_open_csv_files(path=data_path, csv_file=electric_load_data_file)

# Photovoltaic generation
sum_of_photovoltaic_generation_in_per_unit = np.sum(photovoltaic_generation_in_per_unit, 1)
is_winter = True
max_photovoltaic_generation_in_per_unit = np.max(sum_of_photovoltaic_generation_in_per_unit)
photovoltaic_generation_per_unit = sum_of_photovoltaic_generation_in_per_unit / max_photovoltaic_generation_in_per_unit

rated_photovoltaic_kilowatts = 400

# STEP 1: setup parameters
simulation_time_series_resolution_in_minutes = 1
simulation_time_series_resolution_in_hours = simulation_time_series_resolution_in_minutes / 60

energy_management_system_time_series_resolution_in_minutes = 15
energy_management_system_time_series_resolution_in_hours = \
    energy_management_system_time_series_resolution_in_minutes / 60

# Electric Vehicle (EV) parameters
seed = 1000  # Used by OPEN originally
random_seed = np.random.seed(seed)
number_of_electric_vehicles = 120
max_battery_capacity_in_kilowatts_per_hour = 30
max_battery_charging_power_in_kilowatts = 7
electric_vehicle_arrival_time_start = 12
electric_vehicle_arrival_time_end = 22
electric_vehicle_departure_time_start = 5
electric_vehicle_departure_time_end = 8
electric_vehicle_fleet = ElectricVehicleFleet(random_seed=random_seed,
                                              number_of_electric_vehicles=number_of_electric_vehicles,
                                              max_battery_capacity_in_kilowatts_per_hour=
                                              max_battery_capacity_in_kilowatts_per_hour,
                                              max_electric_vehicle_charging_power=
                                              max_battery_charging_power_in_kilowatts,
                                              electric_vehicle_arrival_time_start=
                                              electric_vehicle_arrival_time_start,
                                              electric_vehicle_arrival_time_end=electric_vehicle_arrival_time_end,
                                              electric_vehicle_departure_time_start=
                                              electric_vehicle_departure_time_start,
                                              electric_vehicle_departure_time_end=
                                              electric_vehicle_departure_time_end
                                              )

electric_vehicle_fleet.check_electric_vehicle_fleet_charging_feasibility()
if not electric_vehicle_fleet.is_electric_vehicle_fleet_feasible_for_the_system:
    raise ValueError('The electric vehicle fleet is not feasible for the system')

# Building parameters
max_inside_degree_celsius = 18
min_inside_degree_celsius = 16
initial_inside_degree_celsius = 17
max_consumed_electric_heating_kilowatts = 90
max_consumed_electric_cooling_kilowatts = 200
heat_pump_coefficient_of_performance = 3
chiller_coefficient_of_performance = 1

building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = 500
building_thermal_resistance_in_degree_celsius_per_kilowatts = 0.0337

market_time_interval_in_hours = energy_management_system_time_series_resolution_in_hours

# TODO: update prices from https://www.ofgem.gov.uk/publications/feed-tariff-fit-tariff-table-1-april-2021
export_prices_in_pounds_per_kilowatt_hour = 0.04  # money received of net exports
peak_period_import_prices_in_pounds_per_kilowatt_hour = 0.07
peak_period_hours_per_day = 7
valley_period_import_prices_in_pounds_per_kilowatt_hour = 0.15
valley_period_hours_per_day = 17
demand_charge_in_pounds_per_kilowatt = 0.10  # price per kW for the maximum demand
max_import_kilowatts = 500
max_export_kilowatts = -500
offered_kilowatts_in_frequency_response = 0
max_frequency_response_state_of_charge = 0.6
min_frequency_response_state_of_charge = 0.4
frequency_response_price_in_pounds_per_kilowatt_hour = 0.005

offered_kilowatts_in_frequency_response = 0
max_frequency_response_state_of_charge = 0.6
min_frequency_response_state_of_charge = 0.4
frequency_response_price_in_pounds_per_kilowatt_hour = 0.005

# STEP 2: setup the network
network = pp.create_empty_network()
