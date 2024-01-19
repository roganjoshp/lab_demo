from .config import Config
from .util import chunk

from math import exp

import random

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# For testing so our CSVs will line up
np.random.seed(42)


class Solver:
    
    def __init__(
        self,
        problem,
        iterations,
        temperature,
        cooling_rate,
        turn_off_pct,
        min_swap_hours = 8,
        overproduction_penalty = 1,
        missed_production_penalty = 15,
        config: Config = Config()
    ):
        self.problem = problem
        self.config = config
        self._product_names = problem.forecast.columns
        self._forecast = self.problem.forecast.copy()
        self.min_swap_hours = min_swap_hours
        
        # Input data containers
        self._demands = {}
        
        # Here we distinguish between "production" and "productivity".
        # The former is how much of a product we actually make and the latter 
        # is how much stuff a machine can be making at that time
        self._productivity_map = {}
        
        # # Convert product names to ints
        # self._product_id_map = {}
        # self._produce_id_reverse_map = {}
        
        # Keep track of all machines
        self._machine_irr = self.config.MACHINE_STATS
        self._machine_product_map = {}
        
        # Simulated annealing params
        self.temperature = temperature
        self.cooling_rate = cooling_rate
        self.iterations = iterations
        self.turn_off_pct = turn_off_pct / 100
        self.dice_rolls = np.random.random(size=self.iterations)
        
        # Algo params
        self.overproduction_penalty = overproduction_penalty
        self.missed_production_penalty = missed_production_penalty
        
        # Swaps
        self._machine_swaps = []
        self._product_swaps = []
        self._possible_swap_indices = {}
        self._swap_indices = []
        
        # Solutions
        self._solution = {}
        self._best_ever_solution = {}
        self._best_ever_cost = np.inf
        self._solution_costs = []
        self._product_cost_contributions = {}
        self._production_map = {}
        
        self._solved = False
               
    def _disaggregate_forecast(self):
        """
        Get an object of {machine_id: [hourly_demands]}
        """
        
        for column in self._product_names:
            self._demands[column] = (self._forecast[column] * 100).values
            self._demands[column] = self._demands[column].astype(np.float64)
            
    def _create_productivity_map(self):
        
        # The first thing to do is to assume the machine can produce 24/7 at 
        # its ideal run rate, so fill the PRODUCTIVITY map at max capacity
        for machine in self.problem.machines:
            self._productivity_map[machine.id] = np.full(
                len(self._forecast) - 1, # We don't get the last hour 
                machine.hourly_production
            )
        
        # Initialise the actual PRODUCTION to be zeros while we're here
        for product, hours in self._demands.items():
            self._production_map[product] = np.zeros(
                len(hours),
                dtype=np.float64
            )

        df = pd.DataFrame(self._production_map)
        df.to_csv('production_map.csv')
        
        self._forecast.to_csv('forecast.csv')
        
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
            
            # Now prune down the machine productivity. We use the shift pattern
            # as a mask over the previous array simply through multiplication.
            # When the machine is on, you multiply by 1 and otherwise it gets
            # multiplied by 0. If there is a half hour break in between, then
            # productivity is multiplied by 0.5 etc.
            shift = np.array(shift)
            self._productivity_map[machine.id] = (
                (self._productivity_map[machine.id] * shift).astype(np.float64)
            )

    def _create_product_swap_map(self):
        
        for machine in self.problem.machines:
            self._machine_product_map[machine.id] = [
                product.name for product in machine._products
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
            
    def _create_initial_solution(self):
        """
        Generate a random starting solution
        """
        
        df = pd.DataFrame(self._demands)
        df.to_csv('demands.csv', index=False)
        df = pd.DataFrame(self._productivity_map)
        df.to_csv('productivity_map.csv', index=False)
        
        for machine_id, _ in self._productivity_map.items():
            self._solution[machine_id] = np.full(
                len(self._forecast), "",
                dtype="U20"
            )
            
            for index in self._possible_swap_indices[machine_id]:
                
                product = random.choice(self._machine_product_map[machine_id])

                hour_block = self.min_swap_hours
                
                self._solution[machine_id][index:index+hour_block] = (
                    product
                )
                
                self._production_map[product][index:index+hour_block] += (
                    self._machine_irr[machine_id]['ideal_run_rate']
                )
        
        df = pd.DataFrame(self._production_map)
        df.to_csv('initial_solution_production_map.csv')
        
        # Now need to cumsum up the production
        for product, production in self._production_map.items():
            self._production_map[product] = production.cumsum()
            
        df = pd.DataFrame(self._production_map)
        df.to_csv('cumulative_production.csv', index=False)
        
        # For human readability
        df = pd.DataFrame(self._solution)
        df.to_csv("solution.csv", index=False)
        
    def _get_initial_solution_cost(self):
        
        total_cost = 0
        
        for product in self._production_map.keys():
            production = self._production_map[product]
            cost = self.get_cost(product, production)
            self._product_cost_contributions[product] = cost
            total_cost += cost
        
        return total_cost
        
    def get_cost(
        self,
        product,
        production
    ):
        cost = 0
        
        demand = self._demands[product]
        
        missed_production = (
            (demand - production).clip(0).sum() 
            * self.missed_production_penalty
        )
        
        cost += missed_production
        
        overproduction = (
            (production - demand).clip(0).sum() 
            * self.overproduction_penalty
        )
        
        cost += overproduction
        
        return cost
    
    def _do_swap(
        self,
        machine,
        start_index,
        new_product
    ):
        
        # Payload we want to send back
        rtn = {}
        
        # First add a short-circuit. If we're already making Product_1 and we 
        # want to swap to Product_1 then that's pointless, so break out
        current_product = self._solution[machine][start_index]
        if new_product == current_product:
            return
        
        # Initialise both just incase either the old or the new product is "0"
        swap_out_cost = 0
        swap_in_cost = 0
        
        # Does this swap improve or degrade our solution?
        cost_movement = 0
        
        machine_solution = self._solution[machine].copy()
        
        # The end of the slice we want to look at
        shift_end = start_index + self.min_swap_hours
        
        # Find the machine PRODUCTIVITY for the shift we want to swap
        shift_prod = self._productivity_map[machine][start_index:shift_end]
        
        # Find the total PRODUCTION that will be lost from one product to 
        # be gained by another, by changing this machine's schedule
        hourly_prod = shift_prod.cumsum()
        total_prod = shift_prod.sum()
        
        # TODO this is bad design on the fact I have ints and strings coming
        # through here but no time yet to see where this happens
        if current_product != 0 and current_product != '0':
            
            # Make sure we don't trample our global state in case we don't want 
            # to accept this new solution
            current_prod_production = (
                self._production_map[current_product].copy()
            )
                    
            # First snip out the PRODUCTION from the existing product
            current_prod_production[start_index:shift_end] -= hourly_prod
            current_prod_production[start_index+shift_end:] -= total_prod
            
            # Find the new solution cost for this loss of productivity
            swap_out_cost = self.get_cost(
                current_product,
                current_prod_production
            )
            current_prod_existing_cost = (
                self._product_cost_contributions[current_product]
            )
            
            cost_movement += swap_out_cost - current_prod_existing_cost
            
            rtn['current_prod_production'] = current_prod_production
            rtn['current_prod_cost_contrib'] = swap_out_cost
            rtn['current_product'] = current_product
            
        else:
            rtn['current_product'] = 0
        
        if new_product != 0 and new_product != "0":
            
            new_prod_production = self._production_map[new_product].copy()

            # Now add in the production of the new product
            new_prod_production[start_index:shift_end] += hourly_prod
            new_prod_production[start_index+shift_end:] += total_prod
            
            swap_in_cost = self.get_cost(new_product, new_prod_production)
            new_prod_existing_cost = (
                self._product_cost_contributions[new_product]
            )

            cost_movement += swap_in_cost - new_prod_existing_cost
            
            rtn['new_prod_production'] = new_prod_production
            rtn['new_prod_cost_contrib'] = swap_in_cost
            
        # Reflect the change in the solution itself
        machine_solution[start_index:shift_end] = new_product
        
        rtn['new_solution'] = machine_solution
        rtn['cost_movement'] = cost_movement
        
        return rtn
        
    def solve(self):
        
        self._disaggregate_forecast()
        self._create_productivity_map()
        self._create_product_swap_map()
        self._find_swap_indices()
        self._create_swaps()
        self._create_initial_solution()
        
        # Initialise our best solution and cost 
        self._best_ever_solution = self._solution.copy()
        self._best_ever_cost = self._get_initial_solution_cost()
        _current_cost = self._best_ever_cost
        
        for x in range(self.iterations):
            
            # First pick our machine to target in this atomic swap
            machine_swap = self._machine_swaps[x]
            
            # Now find the start hour of the production we want to swap
            hour = self._swap_indices[x]
            
            # Find the product we want to swap to
            new_product = self._product_swaps[x]
            
            change = self._do_swap(machine_swap, hour, new_product)
            
            if change is not None:
                if change['cost_movement'] < 0:
                    # Accept the solution unconditionally
                    
                    old_product = change['current_product']
                    
                    if old_product != 0:
                        self._production_map[old_product] = (
                            change['current_prod_production'].copy()
                        )
                        self._product_cost_contributions[old_product] = (
                            change['current_prod_cost_contrib']
                        )
                        
                    if new_product != 0:
                        self._production_map[new_product] = (
                            change['new_prod_production'].copy()
                        )
                        self._product_cost_contributions[new_product] = (
                            change['new_prod_cost_contrib']
                        )
                        
                    self._solution[machine_swap] = (
                        change['new_solution'].copy()
                    )
                    _current_cost += change['cost_movement']
                    self._solution_costs.append([x, _current_cost])
                    
                    # Check if we beat our best ever
                    if _current_cost < self._best_ever_cost:
                        self._best_ever_cost = _current_cost
                        self._best_ever_solution = self._solution.copy()
                    
                else:
                    # MAYBE accept the solution
                    dice_roll = self.dice_rolls[x]
                    
                    acceptance = exp(
                        (-change['cost_movement'] / _current_cost ) * 100
                      / self.temperature + 0.00001)
                    
                    if dice_roll < acceptance:
                        old_product = change['current_product']
                        
                        if old_product != 0:
                            self._production_map[old_product] = (
                                change['current_prod_production'].copy()
                            )
                            self._product_cost_contributions[old_product] = (
                                change['current_prod_cost_contrib']
                            )
                            
                        if new_product != 0:
                            self._production_map[new_product] = (
                                change['new_prod_production'].copy()
                            )
                            self._product_cost_contributions[new_product] = (
                                change['new_prod_cost_contrib']
                            )
                            
                        self._solution[machine_swap] = (
                            change['new_solution'].copy()
                        )
                        _current_cost += change['cost_movement']
                        self._solution_costs.append([x, _current_cost])
                    
            self.temperature *= self.cooling_rate
        
        self._solved = True
            
    def plot_solution_convergence(self):
        
        if not self._solved:
            raise RuntimeError("Problem has not been solved!")
                    
        iterations = [item[0] for item in self._solution_costs]
        costs = [item[1] for item in self._solution_costs]
        
        plt.plot(iterations, costs)
        plt.show()
        