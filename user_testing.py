from lab_demo import (
    Problem,
    SalesForecast
)

# This is our collection for all the moving parts
problem = Problem()

sales_forecast = SalesForecast('data_files/sales_forecast.csv')
sales_forecast.interpolate_forecast()

# Try hashing out the previous line. The Problem class knows it's wrong
# because it hasn't been interpolated first. It can see its *state*
problem.add_forecast(sales_forecast)

