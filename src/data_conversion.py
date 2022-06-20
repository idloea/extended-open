import numpy as np
import pandas as pd


def convert_10_min_data_to_1_min_data(data: pd.DataFrame) -> np.ndarray:
    dates = data['Date'].unique()
    one_minute_data = pd.DataFrame(columns=data.columns)
    for date in dates:
        specific_date_data = data[data['Date'] == date]
        specific_date_data = specific_date_data.asfreq(freq='60S', method='pad')
        one_minute_data = pd.concat([one_minute_data, specific_date_data])
    return one_minute_data
