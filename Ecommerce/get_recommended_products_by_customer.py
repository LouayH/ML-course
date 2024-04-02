from db import *
import pickle

def task(customer_id, limit):
  filename = "classification-model"

  model = pickle.load(open(filename, "rb"))
  recommended_products = get_recommended_products_by_customer(model, customer_id, limit)

  return recommended_products