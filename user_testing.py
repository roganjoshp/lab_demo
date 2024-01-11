'''
This script is just to illustrate how a user might interact with your API
'''

from lab_demo import (
    Machine,
    Problem,
    SalesForecast
)

# This is our collection for all the moving parts
problem = Problem()

sales_forecast = SalesForecast('data_files/sales_forecast.csv')
# <any number of things here>
sales_forecast.interpolate_forecast()

# Try hashing out the previous line. The Problem class knows it's wrong
# because it hasn't been interpolated first. It can see its *state*
problem.add_forecast(sales_forecast)

# Try setting machine_id as duplicate values
machine_1 = Machine(machine_id=1, shift_pattern='6-2')
machine_2 = Machine(machine_id=2, shift_pattern='2-10')
machine_3 = Machine(machine_id=3, shift_pattern='6-2 and 2-10')
machine_4 = Machine(machine_id=4, shift_pattern='2-10')

