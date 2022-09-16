import pandas as pd
from src.data_conversion import convert_10_min_data_to_1_min_data
from src.read import read_meteo_navarra_solar_radiation_data

file_path = 'data/solar_radiation/pamplona/10_min/2021_2022_pamplona_upna_10_min_solar_radiation.xlsx'
data_10_min_frequency = read_meteo_navarra_solar_radiation_data(file_path=file_path)
data_1_min_frequency = convert_10_min_data_to_1_min_data(data=data_10_min_frequency)

dates = data_1_min_frequency['Date'].unique()
one_minute_data = pd.DataFrame(columns=data_1_min_frequency.columns)
for date in dates:
    specific_date_data = data_1_min_frequency[data_1_min_frequency['Date'] == date]
    specific_date_data = specific_date_data.asfreq(freq='60S', method='pad')
    series_to_save = specific_date_data['Global_radiation_W/m2']
    dataframe_to_save = pd.DataFrame(series_to_save)
    dataframe_to_save.reset_index(drop=True, inplace=True)
    dataframe_to_save.rename(columns={'Global_radiation_W/m2': '0'}, inplace=True)
    dataframe_to_save.to_csv(f'data/solar_radiation/pamplona/1_min/{date}_pamplona.csv')

global_radiation_in_watts_per_square_meter = data_1_min_frequency['Global_radiation_W/m2']

