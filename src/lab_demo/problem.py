from lab_demo import SalesForecast

import pandas as pd


class Problem:
    
    def __init__(self):
        self.machines = []
        self.forecast = pd.DataFrame()
        self._is_built = False
        self._payload = {}
        
    def add_machine(self, machine):
        self.machines.append(machine)
    
    def add_forecast(self, forecast):
        
        if not isinstance(forecast, SalesForecast):
            raise TypeError("Not a forecast!")
        
        if not forecast._is_interpolated:
            raise RuntimeError("Forecast must be interpolated first!")
        
        self.forecast = forecast.forecast
        
    def build(self):
        print(self.forecast.head())