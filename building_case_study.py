import sys
import numpy as np
from src import assets, energy_system
from src.electric_vehicles import ElectricVehicleFleet
from src.markets import get_market
from src.plot.plots import plot_demand_base_and_total_imported_power, plot_building_internal_temperature, \
    plot_hvac_consumed_active_power_in_kilowatts, plot_ambient_temperature
from src.read import read_open_csv_files, read_case_data_from_yaml_file
import pandapower as pp
from src.temperatures import check_initial_inside_degree_celsius
from src.time_intervals import check_sum_of_daily_periods_in_hours_equals_twenty_four, \
    check_unique_hours_of_daily_periods, check_all_hours_of_daily_periods
from src.ambient_temperature import get_ambient_temperature_in_degree_celsius_by_data_strategy

yaml_file = sys.argv[1]
file_path = 'data/cases'
case_name = yaml_file.split('\\')[-1].split('.')[0]
case_data = read_case_data_from_yaml_file(file_path=file_path, file_name=yaml_file)
data_path = case_data["data_path"]
market_scenario = case_data['market']

# STEP 0: Load data
photovoltaic_generation_data_file = case_data["photovoltaic_generation_data_file"]
photovoltaic_generation_data = read_open_csv_files(path=data_path,
                                                   csv_file=photovoltaic_generation_data_file)
electric_load_data_file = case_data[
    "electric_load_data_file"]  # TODO: why is the demand and the imports different in the final plot?
electric_loads = read_open_csv_files(path=data_path, csv_file=electric_load_data_file)

# Photovoltaic generation
sum_of_photovoltaic_generation_in_per_unit = np.sum(photovoltaic_generation_data, 1)
is_winter = case_data["is_winter"]
max_photovoltaic_generation_in_per_unit = np.max(sum_of_photovoltaic_generation_in_per_unit)
photovoltaic_generation_per_unit = sum_of_photovoltaic_generation_in_per_unit / max_photovoltaic_generation_in_per_unit

rated_photovoltaic_kilowatts = case_data["rated_photovoltaic_kilowatts"]

# STEP 1: setup parameters
simulation_time_series_resolution_in_minutes = case_data["simulation_time_series_resolution_in_minutes"]
simulation_time_series_resolution_in_hours = simulation_time_series_resolution_in_minutes / 60
hours_per_day = 24
number_of_time_intervals_per_day = int(hours_per_day / simulation_time_series_resolution_in_hours)

energy_management_system_time_series_resolution_in_minutes = \
    case_data["energy_management_system_time_series_resolution_in_minutes"]
energy_management_system_time_series_resolution_in_hours = \
    energy_management_system_time_series_resolution_in_minutes / 60
number_of_energy_management_time_intervals_per_day = int(hours_per_day /
                                                         energy_management_system_time_series_resolution_in_hours)

# Electric Vehicle (EV) parameters
seed = 1000  # Used by OPEN originally
random_seed = np.random.seed(seed)
number_of_electric_vehicles = case_data["number_of_electric_vehicles"]
max_battery_capacity_in_kilowatts_per_hour = case_data["max_battery_capacity_in_kilowatts_per_hour"]
max_battery_charging_power_in_kilowatts = case_data["max_battery_charging_power_in_kilowatts"]
electric_vehicle_arrival_time_start = case_data["electric_vehicle_arrival_time_start"]
electric_vehicle_arrival_time_end = case_data["electric_vehicle_arrival_time_end"]
electric_vehicle_departure_time_start = case_data["electric_vehicle_departure_time_start"]
electric_vehicle_departure_time_end = case_data["electric_vehicle_departure_time_end"]
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
max_inside_degree_celsius = case_data["max_inside_degree_celsius"]
min_inside_degree_celsius = case_data["min_inside_degree_celsius"]
initial_inside_degree_celsius = case_data["initial_inside_degree_celsius"]
check_initial_inside_degree_celsius(initial_inside_degree_celsius=initial_inside_degree_celsius,
                                    max_inside_degree_celsius=max_inside_degree_celsius,
                                    min_inside_degree_celsius=min_inside_degree_celsius)
max_consumed_electric_heating_kilowatts = case_data["max_consumed_electric_heating_kilowatts"]
max_consumed_electric_cooling_kilowatts = case_data["max_consumed_electric_cooling_kilowatts"]
heat_pump_coefficient_of_performance = case_data["heat_pump_coefficient_of_performance"]
chiller_coefficient_of_performance = case_data["chiller_coefficient_of_performance"]

building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = \
    case_data["building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius"]
building_thermal_resistance_in_degree_celsius_per_kilowatts = \
    case_data["building_thermal_resistance_in_degree_celsius_per_kilowatts"]

market_time_interval_in_hours = energy_management_system_time_series_resolution_in_hours

export_prices_in_euros_per_kilowatt_hour = case_data["export_prices_in_euros_per_kilowatt_hour"]
import_periods = case_data["import_periods"]
import_period_prices = None
if market_scenario == 'Spanish':
    check_sum_of_daily_periods_in_hours_equals_twenty_four(periods=import_periods)
    check_unique_hours_of_daily_periods(periods=import_periods)
    check_all_hours_of_daily_periods(periods=import_periods)
    import_period_prices = case_data["import_period_prices"]
demand_charge_in_euros_per_kilowatt = case_data["demand_charge_in_euros_per_kilowatt"]
max_import_kilowatts = case_data["max_import_kilowatts"]
max_export_kilowatts = case_data["max_export_kilowatts"]
offered_kilowatts_in_frequency_response = case_data["offered_kilowatts_in_frequency_response"]
max_frequency_response_state_of_charge = case_data["max_frequency_response_state_of_charge"]
min_frequency_response_state_of_charge = case_data["min_frequency_response_state_of_charge"]
frequency_response_price_in_euros_per_kilowatt_hour = case_data["frequency_response_price_in_euros_per_kilowatt_hour"]

# STEP 2: set up the network
network = pp.create_empty_network()

grid_1_voltage_level_in_kilo_volts: int = case_data["grid_1_voltage_level_in_kilo_volts"]
grid_2_voltage_level_in_kilo_volts: float = case_data["grid_2_voltage_level_in_kilo_volts"]
grid_3_voltage_level_in_kilo_volts: float = case_data["grid_3_voltage_level_in_kilo_volts"]

bus_1 = pp.create_bus(network, vn_kv=grid_1_voltage_level_in_kilo_volts, name="bus 1")
bus_2 = pp.create_bus(network, vn_kv=grid_2_voltage_level_in_kilo_volts, name="bus 2")
bus_3 = pp.create_bus(network, vn_kv=grid_3_voltage_level_in_kilo_volts, name="bus 3")

pp.create_ext_grid(network, bus=bus_1, vm_pu=1.0, name="Grid Connection")

high_voltage_bus = bus_1
low_voltage_bus = bus_2

transformer_apparent_power_in_mega_volt_ampere = case_data["transformer_apparent_power_in_mega_volt_ampere"]
trafo_std_type = f"{transformer_apparent_power_in_mega_volt_ampere} MVA {grid_1_voltage_level_in_kilo_volts}" \
                 f"/{grid_2_voltage_level_in_kilo_volts} kV"
trafo = pp.create_transformer(network, hv_bus=high_voltage_bus, lv_bus=low_voltage_bus, std_type=trafo_std_type,
                              name="Trafo")

length_from_bus_2_to_bus_3_in_km = case_data["length_from_bus_2_to_bus_3_in_km"]
line = pp.create_line(network, from_bus=bus_2, to_bus=bus_3, length_km=length_from_bus_2_to_bus_3_in_km,
                      std_type="NAYY 4x50 SE", name="Line")

number_of_buses = network.bus['name'].size

# STEP 3: setup the assets
storage_assets = []
building_assets = []
non_distpachable_assets = []

photovoltaic_active_power_in_kilowatts = -photovoltaic_generation_per_unit * rated_photovoltaic_kilowatts  # Negative as it generates energy
photovoltaic_reactive_power_in_kilovolt_ampere = np.zeros(number_of_time_intervals_per_day)

non_dispatchable_photovoltaic_asset = assets.NonDispatchableAsset(
    simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours, bus_id=bus_3,
    active_power_in_kilowatts=photovoltaic_active_power_in_kilowatts,
    reactive_power_in_kilovolt_ampere_reactive=photovoltaic_reactive_power_in_kilovolt_ampere)
non_distpachable_assets.append(non_dispatchable_photovoltaic_asset)

electric_load_active_power_in_kilowatts = np.sum(electric_loads, 1)
electric_load_reactive_power_in_kilovolt_ampere_reactive = np.zeros(number_of_time_intervals_per_day)
non_dispatchable_electric_load_at_bus_3 = assets.NonDispatchableAsset(
    simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours, bus_id=bus_3,
    active_power_in_kilowatts=electric_load_active_power_in_kilowatts,
    reactive_power_in_kilovolt_ampere_reactive=electric_load_reactive_power_in_kilovolt_ampere_reactive)
non_distpachable_assets.append(non_dispatchable_electric_load_at_bus_3)

ambient_temperature_in_degree_celsius = get_ambient_temperature_in_degree_celsius_by_data_strategy(
    case_data=case_data,
    number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day)

# Building asset at bus 3
bus_id_building = bus_3
building = assets.BuildingAsset(max_inside_degree_celsius=max_inside_degree_celsius,
                                min_inside_degree_celsius=min_inside_degree_celsius,
                                max_consumed_electric_heating_kilowatts=max_consumed_electric_heating_kilowatts,
                                max_consumed_electric_cooling_kilowatts=max_consumed_electric_cooling_kilowatts,
                                initial_inside_degree_celsius=initial_inside_degree_celsius,
                                building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius=
                                building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius,
                                building_thermal_resistance_in_degree_celsius_per_kilowatts=
                                building_thermal_resistance_in_degree_celsius_per_kilowatts,
                                heat_pump_coefficient_of_performance=heat_pump_coefficient_of_performance,
                                chiller_coefficient_of_performance=chiller_coefficient_of_performance,
                                ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius,
                                bus_id=bus_id_building,
                                simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours,
                                energy_management_system_time_series_resolution_in_hours=
                                energy_management_system_time_series_resolution_in_hours)

building_assets.append(building)

# STEP 4: setup the market
bus_id_market = bus_1
market = get_market(case_data=case_data,
                    import_period_prices=import_period_prices,
                    network_bus_id=bus_id_market,
                    market_time_series_resolution_in_hours=market_time_interval_in_hours,
                    export_prices_in_euros_per_kilowatt_hour=export_prices_in_euros_per_kilowatt_hour,
                    import_periods=import_periods,
                    max_demand_charge_in_euros_per_kilowatt_hour=demand_charge_in_euros_per_kilowatt,
                    max_import_kilowatts=max_import_kilowatts,
                    max_export_kilowatts=max_export_kilowatts,
                    offered_kilowatt_in_frequency_response=offered_kilowatts_in_frequency_response,
                    max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                    min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                    frequency_response_price_in_euros_per_kilowatt_hour=
                    frequency_response_price_in_euros_per_kilowatt_hour)

# STEP 5: setup the energy system
energy_system = energy_system.EnergySystem(storage_assets=storage_assets,
                                           non_dispatchable_assets=non_distpachable_assets,
                                           network=network,
                                           market=market,
                                           simulation_time_series_resolution_in_hours=
                                           simulation_time_series_resolution_in_hours,
                                           energy_management_system_time_series_resolution_in_hours=
                                           energy_management_system_time_series_resolution_in_hours,
                                           building_assets=building_assets)

# STEP 6: simulate the energy system:
output = energy_system.simulate_network()
buses_voltage_angle_in_degrees = output['buses_voltage_angle_in_degrees']
buses_active_power_in_kilowatts = output['buses_active_power_in_kilowatts']
buses_reactive_power_in_kilovolt_ampere_reactive = output['buses_reactive_power_in_kilovolt_ampere_reactive']
market_active_power_in_kilowatts = output['market_active_power_in_kilowatts']
market_reactive_power_in_kilovolt_ampere_reactive = output['market_reactive_power_in_kilovolt_ampere_reactive']
buses_voltage_in_per_unit = output['buses_voltage_in_per_unit']
imported_active_power_in_kilowatts = \
    output['imported_active_power_in_kilowatts']
exported_active_power_in_kilowatts = \
    output['exported_active_power_in_kilowatts']
building_power_consumption_in_kilowatts = \
    output['building_power_consumption_in_kilowatts']
active_power_demand_in_kilowatts = \
    output['active_power_demand_in_kilowatts']
active_power_demand_base_in_kilowatts = np.zeros(number_of_time_intervals_per_day)

for non_dispatchable_asset in range(len(non_distpachable_assets)):
    bus_id = non_distpachable_assets[non_dispatchable_asset].bus_id
    active_power_demand_base_in_kilowatts += non_distpachable_assets[non_dispatchable_asset].active_power_in_kilowatts

revenue = \
    round(market.calculate_revenue(-market_active_power_in_kilowatts, simulation_time_series_resolution_in_hours), 2)
print('Revenue in euros:', revenue)

plot_demand_base_and_total_imported_power(
    simulation_time_series_resolution_in_hours=simulation_time_series_resolution_in_hours,
    number_of_time_intervals_per_day=number_of_time_intervals_per_day,
    active_power_demand_base_in_kilowatts=active_power_demand_base_in_kilowatts,
    market_active_power_in_kilowatts=market_active_power_in_kilowatts, case=case_name, revenue=revenue)

plot_ambient_temperature(
    energy_management_system_time_series_resolution_in_hours=energy_management_system_time_series_resolution_in_hours,
    number_of_energy_management_time_intervals_per_day=number_of_energy_management_time_intervals_per_day,
    ambient_temperature_in_degree_celsius=ambient_temperature_in_degree_celsius, case=case_name)

number_of_buildings = len(building_assets)
plot_building_internal_temperature(number_of_buildings=number_of_buildings,
                                   energy_management_system_time_series_resolution_in_hours=
                                   energy_management_system_time_series_resolution_in_hours,
                                   number_of_energy_management_time_intervals_per_day=
                                   number_of_energy_management_time_intervals_per_day,
                                   building_assets=building_assets, case=case_name)

plot_hvac_consumed_active_power_in_kilowatts(number_of_buildings=number_of_buildings,
                                             simulation_time_series_resolution_in_hours=
                                             simulation_time_series_resolution_in_hours,
                                             number_of_time_intervals_per_day=number_of_time_intervals_per_day,
                                             energy_management_system_time_series_resolution_in_hours=
                                             energy_management_system_time_series_resolution_in_hours,
                                             number_of_energy_management_time_intervals_per_day=
                                             number_of_energy_management_time_intervals_per_day,
                                             building_assets=building_assets,
                                             max_consumed_electric_heating_kilowatts=None,
                                             max_consumed_electric_cooling_kilowatts=
                                             max_consumed_electric_cooling_kilowatts, case=case_name)

plot_hvac_consumed_active_power_in_kilowatts(number_of_buildings=number_of_buildings,
                                             simulation_time_series_resolution_in_hours=
                                             simulation_time_series_resolution_in_hours,
                                             number_of_time_intervals_per_day=number_of_time_intervals_per_day,
                                             energy_management_system_time_series_resolution_in_hours=
                                             energy_management_system_time_series_resolution_in_hours,
                                             number_of_energy_management_time_intervals_per_day=
                                             number_of_energy_management_time_intervals_per_day,
                                             building_assets=building_assets,
                                             max_consumed_electric_heating_kilowatts=
                                             max_consumed_electric_heating_kilowatts,
                                             max_consumed_electric_cooling_kilowatts=None, case=case_name)
