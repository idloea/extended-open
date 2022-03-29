import numpy as np
from src import assets, markets, energy_system
from src.electric_vehicles import ElectricVehicleFleet
from src.plot.plots import plot_demand_base_and_total_imported_power
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
hours_per_day = 24
number_of_time_intervals_per_day = int(hours_per_day / simulation_time_series_resolution_in_hours)

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

grid_1_voltage_level_in_kilo_volts: int = 20
grid_2_voltage_level_in_kilo_volts: float = 0.4
grid_3_voltage_level_in_kilo_volts: float = 0.4

bus_1 = pp.create_bus(network, vn_kv=grid_1_voltage_level_in_kilo_volts, name="bus 1")
bus_2 = pp.create_bus(network, vn_kv=grid_2_voltage_level_in_kilo_volts, name="bus 2")
bus_3 = pp.create_bus(network, vn_kv=grid_3_voltage_level_in_kilo_volts, name="bus 3")

pp.create_ext_grid(network, bus=bus_1, vm_pu=1.0, name="Grid Connection")

high_voltage_bus = bus_1
low_voltage_bus = bus_2

transformer_apparent_power_in_mega_volt_ampere = 0.4
trafo_std_type = f"{transformer_apparent_power_in_mega_volt_ampere} MVA {grid_1_voltage_level_in_kilo_volts}" \
                 f"/{grid_2_voltage_level_in_kilo_volts} kV"
trafo = pp.create_transformer(network, hv_bus=high_voltage_bus, lv_bus=low_voltage_bus, std_type=trafo_std_type,
                              name="Trafo")

length_from_bus_2_to_bus_3_in_km = 0.1
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

# Building asset at bus 3
if is_winter:
    ambient_degree_celsius = 10
else:
    ambient_degree_celsius = 22

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
                                ambient_temperature_in_degree_celsius=ambient_degree_celsius,
                                bus_id=bus_id_building,
                                simulation_time_series_hour_resolution=simulation_time_series_resolution_in_hours,
                                energy_management_system_time_series_resolution_in_hours=
                                energy_management_system_time_series_resolution_in_hours)

building_assets.append(building)

# STEP 4: setup the market
bus_id_market = bus_1
market = markets.Market(network_bus_id=bus_id_market,
                        market_time_series_minute_resolution=market_time_interval_in_hours,
                        export_prices_in_pounds_per_kilowatt_hour=export_prices_in_pounds_per_kilowatt_hour,
                        peak_period_import_prices_in_pounds_per_kilowatt_hour=
                        peak_period_import_prices_in_pounds_per_kilowatt_hour,
                        peak_period_hours_per_day=peak_period_hours_per_day,
                        valley_period_import_prices_in_pounds_per_kilowatt_hour=
                        valley_period_import_prices_in_pounds_per_kilowatt_hour,
                        valley_period_hours_per_day=valley_period_hours_per_day,
                        max_demand_charge_in_pounds_per_kWh=demand_charge_in_pounds_per_kilowatt,
                        max_import_kilowatts=max_import_kilowatts,
                        max_export_kilowatts=max_export_kilowatts,
                        offered_kW_in_frequency_response=offered_kilowatts_in_frequency_response,
                        max_frequency_response_state_of_charge=max_frequency_response_state_of_charge,
                        min_frequency_response_state_of_charge=min_frequency_response_state_of_charge,
                        frequency_response_price_in_pounds_per_kilowatt_hour=
                        frequency_response_price_in_pounds_per_kilowatt_hour)

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

revenue = market.calculate_revenue(-market_active_power_in_kilowatts, simulation_time_series_resolution_in_hours)
print('Revenue in pounds:', revenue)

plot_demand_base_and_total_imported_power(simulation_time_series_resolution_in_hours=
                                          simulation_time_series_resolution_in_hours,
                                          number_of_time_intervals_per_day=number_of_time_intervals_per_day,
                                          active_power_demand_base_in_kilowatts=active_power_demand_base_in_kilowatts,
                                          market_active_power_in_kilowatts=market_active_power_in_kilowatts)

