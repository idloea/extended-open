from building_case_study import run

if __name__ == "__main__":
    # Photovoltaic generation
    rated_photovoltaic_kilowatts = 400

    # Time series resolutions
    simulation_time_series_resolution_in_minutes = 1
    energy_management_system_time_series_resolution_in_minutes = 15

    # Electric vehicle parameters
    number_of_electric_vehicles = 120
    max_battery_capacity_in_kilowatts_per_hour = 30
    max_battery_charging_power_in_kilowatts = 7
    electric_vehicle_arrival_time_start = 12
    electric_vehicle_arrival_time_end = 22
    electric_vehicle_departure_time_start = 5
    electric_vehicle_departure_time_end = 8

    # Building parameters
    max_inside_degree_celsius = 25  # RITE Tabla 1.4.1.1 Condiciones interiores de diseño (https://www.boe.es/buscar/act.php?id=BOE-A-2007-15820)
    min_inside_degree_celsius = 21  # RITE Tabla 1.4.1.1 Condiciones interiores de diseño (https://www.boe.es/buscar/act.php?id=BOE-A-2007-15820)
    initial_inside_degree_celsius = 21
    max_consumed_electric_heating_kilowatts = 400
    max_consumed_electric_cooling_kilowatts = 400
    heat_pump_coefficient_of_performance = 3  # 1 electric kWh = 3 thermal kWh
    chiller_coefficient_of_performance = 1
    building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius = 500
    building_thermal_resistance_in_degree_celsius_per_kilowatts = 0.0337

    # Cost parameters
    export_prices_in_euros_per_kilowatt_hour = 0.189  # Average between 2022/01/01-2022/09/14 (https://www.esios.ree.es/es/analisis/1739?vis=1&start_date=01-01-2022T00%3A00&end_date=14-09-2022T23%3A55&compare_start_date=31-12-2021T00%3A00&groupby=day&compare_indicators=1013,1014,1015)
    # Spanish Electric Tariff: 6.1TD (https://tarifasgasluz.com/pymes/tarifas-luz/seis-periodos)
    # Iberdrola prices from here: https://tarifasgasluz.com/pymes/tarifas-luz#nueva-tarifa-pyme
    # Periods from here: https://www.electricadealginet.com/wp-content/uploads/7-Industrias-tarifas-6.1-a-6.4.pdf
    import_period_prices = {'P1': 0.1395,
                            'P2': 0.1278,
                            'P3': 0.1110,
                            'P4': 0.1014,
                            'P5': 0.0927,
                            'P6': 0.0871}

    demand_charge_in_euros_per_kilowatt = 0  # Already considered in the import_period_prices
    max_import_kilowatts = 500
    max_export_kilowatts = -500

    # Flexibility
    offered_kilowatts_in_frequency_response = 0
    max_frequency_response_state_of_charge = 0.6
    min_frequency_response_state_of_charge = 0.4
    frequency_response_price_in_euros_per_kilowatt_hour = 0.0059

    # Grid parameters
    grid_1_voltage_level_in_kilo_volts = 20
    grid_2_voltage_level_in_kilo_volts = 0.4
    grid_3_voltage_level_in_kilo_volts = 0.4
    transformer_apparent_power_in_mega_volt_ampere = 0.4
    length_from_bus_2_to_bus_3_in_km = 0.1

    general_case_data = {
        'rated_photovoltaic_kilowatts': rated_photovoltaic_kilowatts,
        'simulation_time_series_resolution_in_minutes': simulation_time_series_resolution_in_minutes,
        'energy_management_system_time_series_resolution_in_minutes':
            energy_management_system_time_series_resolution_in_minutes,
        'number_of_electric_vehicles': number_of_electric_vehicles,
        'max_battery_capacity_in_kilowatts_per_hour': max_battery_capacity_in_kilowatts_per_hour,
        'max_battery_charging_power_in_kilowatts': max_battery_charging_power_in_kilowatts,
        'electric_vehicle_arrival_time_start': electric_vehicle_arrival_time_start,
        'electric_vehicle_arrival_time_end': electric_vehicle_arrival_time_end,
        'electric_vehicle_departure_time_start': electric_vehicle_departure_time_start,
        'electric_vehicle_departure_time_end': electric_vehicle_departure_time_end,
        'max_inside_degree_celsius': max_inside_degree_celsius,
        'min_inside_degree_celsius': min_inside_degree_celsius,
        'initial_inside_degree_celsius': initial_inside_degree_celsius,
        'max_consumed_electric_heating_kilowatts': max_consumed_electric_heating_kilowatts,
        'max_consumed_electric_cooling_kilowatts': max_consumed_electric_cooling_kilowatts,
        'heat_pump_coefficient_of_performance': heat_pump_coefficient_of_performance,
        'chiller_coefficient_of_performance': chiller_coefficient_of_performance,
        'building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius':
            building_thermal_capacitance_in_kilowatts_hour_per_degree_celsius,
        'building_thermal_resistance_in_degree_celsius_per_kilowatts':
            building_thermal_resistance_in_degree_celsius_per_kilowatts,
        'export_prices_in_euros_per_kilowatt_hour': export_prices_in_euros_per_kilowatt_hour,
        'import_period_prices': import_period_prices,
        'demand_charge_in_euros_per_kilowatt': demand_charge_in_euros_per_kilowatt,
        'max_import_kilowatts': max_import_kilowatts,
        'max_export_kilowatts': max_export_kilowatts,
        'offered_kilowatts_in_frequency_response': offered_kilowatts_in_frequency_response,
        'max_frequency_response_state_of_charge': max_frequency_response_state_of_charge,
        'min_frequency_response_state_of_charge': min_frequency_response_state_of_charge,
        'frequency_response_price_in_euros_per_kilowatt_hour': frequency_response_price_in_euros_per_kilowatt_hour,
        'grid_1_voltage_level_in_kilo_volts': grid_1_voltage_level_in_kilo_volts,
        'grid_2_voltage_level_in_kilo_volts': grid_2_voltage_level_in_kilo_volts,
        'grid_3_voltage_level_in_kilo_volts': grid_3_voltage_level_in_kilo_volts,
        'transformer_apparent_power_in_mega_volt_ampere': transformer_apparent_power_in_mega_volt_ampere,
        'length_from_bus_2_to_bus_3_in_km': length_from_bus_2_to_bus_3_in_km

    }

    yaml_files = ['01_january_no_flexibility.yaml',
                  '02_february_no_flexibility.yaml',
                  '03_march_no_flexibility.yaml',
                  '04_april_no_flexibility.yaml',
                  '05_may_no_flexibility.yaml',
                  '06_june_no_flexibility.yaml',
                  '07_july_no_flexibility.yaml',
                  '08_august_no_flexibility.yaml',
                  '09_september_no_flexibility.yaml',
                  '10_october_no_flexibility.yaml',
                  '11_november_no_flexibility.yaml',
                  '12_december_no_flexibility.yaml'
                  ]
    run(yaml_files=yaml_files, general_case_data=general_case_data)
