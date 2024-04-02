from db import *

def task(product_id):
  recommended_products = get_recommended_products_by_product(product_id)

  return recommended_products