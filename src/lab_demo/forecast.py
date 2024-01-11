import os
import pathlib

import pandas as pd


class SalesForecast:
    
    def __init__(self):
        _base_path = pathlib.Path(__file__).parent.resolve()
        _fake_upload_path = os.path.join(
            _base_path, 
            'data_files/sales_forecast.csv'
        )
        
        self.base_forecast = pd.read_csv(_fake_upload_path)
            

if __name__ == '__main__':
    forecast = SalesForecast()
    print(forecast.base_forecast.head())