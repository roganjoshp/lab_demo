from lab_demo.config import Config

import numpy as np
import pandas as pd


class Solver:
    
    def __init__(
        self,
        problem,
        config: Config = Config()
    ):
        self.problem = problem
        self.config = config
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
                len(self._forecast) - 1, # We don't get the last hour 
                machine.hourly_production
            )
        
        self._forecast.to_csv('forecast.csv')
        
        # Now we need to overlay the shift patterns. They need to be expanded
        # out because they only cover a single week
        for i, machine in enumerate(self.problem.machines):
            shift = []
            week_shift = machine.shift_pattern
            # First flatten the dictionary to give us a single week
            for k, v in week_shift.items():
                shift.extend(v)
            
            # Now extend for the total number of weeks
            num_weeks = int(len(self._forecast) / len(shift))
            week_shift = shift.copy()
            for x in range(num_weeks - 1): # We already have the first week
                shift += week_shift
            
            # Now prune down the machine productivity
            shift = np.array(shift)
            self._productivity_map[i] = self._productivity_map[i] * shift