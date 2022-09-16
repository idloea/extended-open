from src.read import read_meteo_navarra_ambient_temperature_csv_data
import datetime


def adapt_ambient_temperature_data_from_solar_time_to_regular_time(read_path: str, read_file: str, time_schedule: str,
                                                                   start_date: str, end_date: str,
                                                                   write_path: str) -> None:

    file_path = read_path + '/' + read_file
    data = read_meteo_navarra_ambient_temperature_csv_data(file_path=file_path)
    if time_schedule == 'winter':
        hours = 1
    elif time_schedule == 'summer':
        hours = 2
    else:
        raise ValueError(f'{time_schedule} is not possible. Write "winter" or "summer" for the time_schedule variable.')
    delta = datetime.timedelta(hours=hours)
    data['DateTime'] = data['DateTime'] + delta
    filtered_data = data[(data['DateTime'] >= start_date) & (data['DateTime'] < end_date)]
    if filtered_data.empty:
        raise ValueError('There is no data for the selected dates')
    saving_date = start_date.replace('-', '')
    csv_file_name = f'{saving_date}_ambient_temperature_upna.csv'
    csv_file_path = write_path + '/' + csv_file_name
    filtered_data.to_csv(path_or_buf=csv_file_path, index=False)
    print(f'{csv_file_name} has been saved to {write_path}')


if __name__ == '__main__':
    read_path = 'data/ambient_temperature/pamplona'
    read_file = '202110_ambient_temperature.csv'
    start_date = '2022-10-15'
    end_date = '2022-10-16'
    time_schedule = 'summer'
    write_path = read_path
    adapt_ambient_temperature_data_from_solar_time_to_regular_time(read_path=read_path, read_file=read_file,
                                                                   time_schedule=time_schedule,
                                                                   start_date=start_date, end_date=end_date,
                                                                   write_path=write_path)

