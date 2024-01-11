import os
import pathlib

import datetime as dt
import pandas as pd


class SalesForecast:
    
    def __init__(self):
        _base_path = pathlib.Path(__file__).parent.resolve()
        _fake_upload_path = os.path.join(
            _base_path, 
            'data_files/sales_forecast.csv'
        )
        
        self.base_forecast = pd.read_csv(_fake_upload_path)
        self.forecast = pd.DataFrame()
        
    def interpolate_forecast(self):
        
        self.forecast = self.base_forecast.copy()
        
        _columns = self.forecast.columns
        
        _blank_week = pd.DataFrame(
            [[0 for _ in _columns]], columns=_columns
        )
        
        # Add in an additional "week" so that interpolation starts at 0
        self.forecast = pd.concat([_blank_week, self.forecast])
    
        # Add in a final "week" so that we have something to interp up to
        self.forecast = pd.concat([self.forecast, _blank_week])
       
        today = dt.date.today()
        days_to_add = 7 - today.weekday()
        next_monday = today + dt.timedelta(days=days_to_add)
        date_range = pd.date_range(start=next_monday, periods=6, freq='W-MON')
        
        self.forecast = self.forecast.set_index(date_range)
        
        print(self.forecast.head(10))
        
        # # Transpose the df and get it at hourly granulatity using interpolate
        # self.forecast = (
        #     self.base_forecast.set_index('Product Name')
        #                       .T
        #                       .set_index(pd.DatetimeIndex(date_range))
        #                       .cumsum()
        # )
        # self.forecast = self.forecast.resample(rule='H').interpolate()
        

if __name__ == '__main__':
    sales_forecast = SalesForecast()
    sales_forecast.interpolate_forecast()
    # print(sales_forecast.forecast.head())