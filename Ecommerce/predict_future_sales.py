from db import *
from autots import AutoTS

def task():
  last_sale_date = get_last_sale_date()
  start_date = last_sale_date - timedelta(days = 60)
  end_date = last_sale_date + timedelta(days = 1, microseconds =  -1)

  data = get_sales_between_two_dates(start_date, end_date)

  # resample
  data["date"] = pd.to_datetime(data["date"])
  data = data.set_index("date")
  data = data.resample("D").mean()
  data["sales"] = data["sales"].fillna(data["sales"].mean())
  data = data.reset_index()

  # predict forecasts
  forecast_length = 10
  model = AutoTS(forecast_length, frequency = "infer")
  model = model.fit(data, date_col = "date", value_col = "sales")

  prediction = model.predict()
  forecast = prediction.forecast

  export_sales_forecast(forecast)