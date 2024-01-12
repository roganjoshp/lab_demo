from lab_demo.config import Config

import numpy as np
import pandas as pd


class Solver:
    
    def __init__(
        self,
        problem,
        iterations = 10000,
        temperature = 10,
        cooling_rate = 0.9999,
        config: Config = Config()
    ):
        self.problem = problem
        self.config = config
        self._product_names = problem.forecast.columns
        self._forecast = self.problem.forecast.copy()
        
        # Map product names to an integer
        self._product_name_map = {}
        
        # Input data containers
        self._demands = {}
        
        # Here we distinguish between "production" and "productivity".
        # The former is how much of a product we actually make and the latter 
        # is how much stuff a machine can be making at that time
        self._productivity_map = {}
        
        # Keep track of all machines
        self._machine_product_map = {}
        
        # Store a list of product ids against a machine id
        self._machine_products = {} 
               
    def _disaggregate_forecast(self):
        """
        Get an object of {machine_id: [hourly_demands]}
        """
        
        for i, column in enumerate(self._product_names):
            self._demands[i] = self._forecast[column].values
            self._product_name_map[column] = i
        
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
            
        # df = pd.DataFrame(self._productivity_map)
        # df.to_csv('prod_map.csv')
    
    def _create_product_swap_map(self):
        
        for machine in self.problem.machines:
            self._machine_product_map[machine.id] = [
                self._product_name_map[product.name] 
                for product in machine._products
            ]
        
        
    