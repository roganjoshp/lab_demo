from .config import Config
from .util import chunk

import random

import numpy as np
import pandas as pd


class Solver:
    
    def __init__(
        self,
        problem,
        iterations = 10000,
        temperature = 10,
        cooling_rate = 0.9999,
        turn_off_pct = 15,
        min_swap_hours = 8,
        config: Config = Config()
    ):
        self.problem = problem
        self.config = config
        self._product_names = problem.forecast.columns
        self._forecast = self.problem.forecast.copy()
        self.min_swap_hours = min_swap_hours
        
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
        
        # Simulated annealing params
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.iterations = iterations
        self.turn_off_pct = turn_off_pct / 100
        
        # Swaps
        self._machine_swaps = []
        self._product_swaps = []
        self._possible_swap_indices = {}
        self._swap_indices = []
        
        # Solutions
        self._solution = {}
        self._best_ever_solution = {}
               
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
        for machine in self.problem.machines:
            self._productivity_map[machine.id] = np.full(
                len(self._forecast) - 1, # We don't get the last hour 
                machine.hourly_production
            )
        
        # self._forecast.to_csv('forecast.csv')
        
        # Now we need to overlay the shift patterns. They need to be expanded
        # out because they only cover a single week
        for machine in self.problem.machines:
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
            self._productivity_map[machine.id] = (
                self._productivity_map[machine.id] * shift
            )

    def _create_product_swap_map(self):
        
        for machine in self.problem.machines:
            self._machine_product_map[machine.id] = [
                self._product_name_map[product.name] 
                for product in machine._products
            ]
            
    def _find_swap_indices(self):
        """ Return list of swappable indices for each machine 
        
        Given that machines only run for certain periods of the day AND the fact 
        that there is a minimum amount of time that a machine can run one 
        product before it can switch again, it's possible to target the indices
        that are eligible to swap vs. just picking starting indices at random.
        
        Swapping at random gives a high chance of swapping in total downtime 
        (useless) in addition to giving product swaps at weird intervals e.g.
        one hour into a shift. This method is not without its flaws - it relies
        on shifts being generally regular in rotation. This is generally true.
        """
        
        for machine_id, productivity in self._productivity_map.items():
            
            starts = []
            arr = productivity.nonzero()[0].tolist()
            seen_indices = set()
            
            for index in arr:
                if index not in seen_indices:
                    starts.append(index)
                    seen_indices.update(
                        list(range(index, index + self.min_swap_hours))
                    )
            self._possible_swap_indices[machine_id] = starts
        
    def _create_swaps(self):
        
        # We know how many iterations we want to do, so we can pre-select all
        # our machines in a single call. If we terminate early, it's still 
        # quicker than calling random() on every iteration, so we can throw 
        # them away
        
        self._machine_swaps = np.random.choice(
            list(self._productivity_map.keys()), self.iterations, replace=True
        )
        
        # Product swaps are more difficult. Since the machine is not
        # specifically pre-determined, we need to iterate this one :(
        # We should actually calculate this in the solver loop itself because
        # of this, but it's cognitively simpler to do it here for the demo
        for machine_id in self._machine_swaps:
            possible_products = self._machine_product_map[machine_id]
            if random.random() < self.turn_off_pct:
                self._product_swaps.append(0)
            else:
                product = random.choice(possible_products)
                self._product_swaps.append(product)
        
            # Now find where we want to put the product
            production_start = random.choice(
                self._possible_swap_indices[machine_id]
            )
            self._swap_indices.append(production_start)
            
    def create_initial_solution(self):
        """
        Generate a random starting solution
        """
        
        # df = pd.DataFrame(self._demands)
        # df.to_csv('demands.csv')
        # df = pd.DataFrame(self._productivity_map)
        # df.to_csv('productivity_map.csv')
        
        for machine_id, _ in self._productivity_map.items():
            self._solution[machine_id] = np.zeros(len(self._forecast))
            
            for index in self._possible_swap_indices[machine_id]:
                product = random.choice(self._machine_product_map[machine_id])
                self._solution[machine_id][index:index+self.min_swap_hours] = (
                    product
                )
        
    def get_cost(self):
        pass
    
    def solve(self):
        pass
        
    
    
            
    