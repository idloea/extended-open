import numpy as np


class ElectricVehicleFleet:
    def __init__(self,
                 random_seed: int,
                 number_of_electric_vehicles: int,
                 max_battery_capacity_in_kilowatts_per_hour: int,
                 max_electric_vehicle_charging_power: int,
                 electric_vehicle_arrival_time_start: int,
                 electric_vehicle_arrival_time_end: int,
                 electric_vehicle_departure_time_start: int,
                 electric_vehicle_departure_time_end: int,
                 start_time_of_the_day: int):

        self.is_electric_vehicle_feasible = False
        self.random_seed = random_seed
        self.number_of_electric_vehicles = number_of_electric_vehicles
        self.max_electric_vehicle_energy_level = max_battery_capacity_in_kilowatts_per_hour
        self.max_electric_vehicle_charging_power = max_electric_vehicle_charging_power
        self.electric_vehicle_arrival_time_start = electric_vehicle_arrival_time_start
        self.electric_vehicle_arrival_time_end = electric_vehicle_arrival_time_end
        self.electric_vehicle_departure_time_start = electric_vehicle_departure_time_start
        self.electric_vehicle_departure_time_end = electric_vehicle_departure_time_end
        self.start_time_of_the_day = start_time_of_the_day

        self.random_electric_vehicle_arrival_time = self.get_random_electric_vehicle_arrival_time()
        self.random_electric_vehicle_departure_time = self.get_random_electric_vehicle_departure_time()
        self.random_electric_vehicle_energy_levels = self.get_random_electric_vehicle_energy_levels()

    def get_random_electric_vehicle_arrival_time(self):
        return np.random.randint(self.electric_vehicle_arrival_time_start * 2,
                                 self.electric_vehicle_arrival_time_end * 2,
                                 self.number_of_electric_vehicles) - self.start_time_of_the_day * 2

    def get_random_electric_vehicle_departure_time(self):
        return np.random.randint(self.electric_vehicle_departure_time_start * 2,
                                 self.electric_vehicle_departure_time_end * 2,
                                 self.number_of_electric_vehicles) - self.start_time_of_the_day * 2

    def get_random_electric_vehicle_energy_levels(self):
        return self.max_electric_vehicle_energy_level * np.random.uniform(0, 1, self.number_of_electric_vehicles)

    def check_electric_vehicle_fleet_charging_feasibility(self):
        for electric_vehicle_number in range(self.number_of_electric_vehicles):
            random_electric_vehicle_departure_time = self.random_electric_vehicle_departure_time[electric_vehicle_number]
            random_electric_vehicle_arrival_time = self.random_electric_vehicle_arrival_time[electric_vehicle_number]
            self.random_electric_vehicle_departure_time[electric_vehicle_number] = \
                np.max([random_electric_vehicle_departure_time, random_electric_vehicle_arrival_time])

            energy_levels = self.random_electric_vehicle_energy_levels[electric_vehicle_number]
            time_between_departure_and_arrival = random_electric_vehicle_departure_time - random_electric_vehicle_arrival_time
            charged_energy_between_departure_and_arrival = \
                self.max_electric_vehicle_charging_power * time_between_departure_and_arrival
            difference_between_max_and_charged_energy_levels = \
                self.max_electric_vehicle_energy_level - charged_energy_between_departure_and_arrival
            self.random_electric_vehicle_energy_levels[electric_vehicle_number] =\
                np.max([energy_levels, difference_between_max_and_charged_energy_levels])

        condition = all(electric_vehicle_energy_level >= 0 for electric_vehicle_energy_level
                        in self.random_electric_vehicle_energy_levels)
        if condition:
            self.is_electric_vehicle_feasible = True
        else:
            pass
