def get_number_of_time_intervals_per_day(time_series_resolution_in_hours: float) -> int:
    hours_per_day = 24
    return int(hours_per_day / time_series_resolution_in_hours)
