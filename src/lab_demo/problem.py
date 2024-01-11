from lab_demo import SalesForecast

import pandas as pd


class Problem:
    
    def __init__(self):
        self.machines = []
        self.forecast = pd.DataFrame()
        
    def add_machine(self, machine):
        self.machines.append(machine)
    
    def add_forecast(self, forecast):
        
        if not isinstance(forecast, SalesForecast):
            raise TypeError("Not a forecast!")
        
        if not forecast._is_interpolated:
            raise RuntimeError("Forecast must be interpolated first!")
        
    def build(self):
        self