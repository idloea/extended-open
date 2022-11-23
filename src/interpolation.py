import numpy as np


def get_extrapolated_array_from_hour_to_minutes(array_in_hours: np.ndarray) -> np.ndarray:
    minutes_per_hour = 60
    array_list = []
    for specific_array_in_hours in array_in_hours:
        array_in_minutes = \
            specific_array_in_hours / minutes_per_hour
        active_power_in_kilowatts_per_hour_in_one_minute_array = \
            np.ones(minutes_per_hour) * array_in_minutes
        array_list.append(
            active_power_in_kilowatts_per_hour_in_one_minute_array)
    return np.vstack(array_list).flatten()
