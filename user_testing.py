'''
This script is just to illustrate how a user might interact with your API
'''

from lab_demo import (
    Machine,
    Problem,
    SalesForecast,
    Solver
)

import random


# This is our container for all the moving parts. We just keep adding to it
problem = Problem()

sales_forecast = SalesForecast('data_files/sales_forecast.csv')
# <any number of things here to interact with the sales_forecast>
sales_forecast.interpolate_forecast()

# Try hashing out the previous line. The Problem class knows it's wrong
# because it hasn't been interpolated first. It can see its *state*
problem.add_forecast(sales_forecast)

# Retrieve the products using a helper function, to give everything in the 
# forecast
products = sales_forecast.get_products()

# Create machines and add a random assortment of possible products to them
# Try setting machine_id as duplicate values
machine_1 = Machine(machine_id=1, shift_pattern='6-2')
mach_1_prods = random.sample(products, random.randint(1,4))
for product in mach_1_prods:
    machine_1.add_product(product)

machine_2 = Machine(machine_id=2, shift_pattern='2-10')
mach_2_prods = random.sample(products, random.randint(1,4))
for product in mach_2_prods:
    machine_2.add_product(product)
    
machine_3 = Machine(machine_id=3, shift_pattern='6-2 and 2-10')
mach_3_prods = random.sample(products, random.randint(1,4))
for product in mach_3_prods:
    machine_3.add_product(product)
    
machine_4 = Machine(machine_id=4, shift_pattern='2-10')
mach_4_prods = random.sample(products, random.randint(1,4))
for product in mach_4_prods:
    machine_4.add_product(product)

# Again, everything goes into our container instance of Problem
problem.add_machine(machine_1)
problem.add_machine(machine_2)
problem.add_machine(machine_3)
problem.add_machine(machine_4)

problem.build()

solver = Solver(
    problem=problem,
    iterations=100,
    temperature=10,
    cooling_rate=0.9,
    turn_off_pct=15)

solver.solve()

# solver.plot_solution_convergence()