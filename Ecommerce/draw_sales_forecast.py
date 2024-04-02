from db import *
import base64
import matplotlib.pyplot as plt

def task():
  forecast = get_sales_forecast()

  plt.figure(figsize = (10, 8))
  plt.title("Sales Forecast")
  plt.plot(forecast["date"], forecast["sales"])
  plt.xlabel("Date")
  plt.ylabel("Total Sales")
  
  filename = "sales-forecast.png"
  plt.savefig(filename, format = "png")
  
  with open(filename, "rb") as image_file:
    image_data = image_file.read()
    base64_image = base64.b64encode(image_data).decode("utf-8")

  return f"data:image/png;base64,{base64_image}"