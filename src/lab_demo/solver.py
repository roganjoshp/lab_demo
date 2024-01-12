import numpy as np
import pandas as pd


class Solver:
    
    def __init__(
        self,
        problem
    ):
        self.problem = problem
        self._product_names = problem.forecast.columns
        self._forecast = self.problem.forecast.copy()
        
        # Input data containers
        self._demands = {}
        # Here we distinguish between "production" and "productivity".
        # The former is how much of a product we actually make and the latter 
        # is how much stuff a machine can be making at that time
        self._productivity_map = {}
        
    def _disaggregate_forecast(self):
        """
        Get an object of {machine_id: [hourly_demands]}
        """
        
        for i, column in enumerate(self._product_names):
            self._demands[i] = self._forecast[column].values
        
    def _create_productivity_map(self):
        
        # The first thing to do is to assume the machine can produce 24/7 at 
        # its ideal run rate
        for i, machine in enumerate(self.problem.machines):
            self._productivity_map[i] = np.full(
                len(self._forecast), 
                machine.hourly_production
            )
        
        df = pd.DataFrame(self._productivity_map) 
        df.to_csv('productivty_map.csv')   
    
    