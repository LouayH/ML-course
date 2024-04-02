import sys
import threading
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods = ["GET"])
def index():
  return ('', 204)

pending_generate_associations_rules = False
@app.route("/generate-associations-rules", methods = ["GET"])
def do_generate_associations_rules():
  if pending_generate_associations_rules:
    result = {
      "success": False,
      "message": "Task is pending"
    }
  else:
    result = {
      "success": True,
      "message": "Task started"
    }

    thread = threading.Thread(target = generate_associations_rules_task)
    thread.start()

  return result

sys.path.append("generate_associations_rules")
def generate_associations_rules_task():
  global pending_generate_associations_rules
  pending_generate_associations_rules = True

  from generate_associations_rules import task
  try:
    task()
    pending_generate_associations_rules = False
  except Exception as e:
    pending_generate_associations_rules = False
    print("Error:", e)

sys.path.append("get_recommended_products_by_product")
@app.route("/get-recommended-products-by-product", methods = ["GET"])
def get_recommended_products_by_product_task():
  from get_recommended_products_by_product import task
  try:
    product_id = request.args.get("product_id")

    if product_id:
      recommended_products = task(product_id)
      result = {
        "success": True,
        "message": {
          "recommended_products": recommended_products
        }
      }
    else:
      result = {
        "success": False,
        "message": "No product id provided"
      }
  except Exception as e:
    result = {
      "success": False,
      "message": f"Error: {e}"
    }

  return result

@app.errorhandler(404)
def notFound(error):
  result = {
    "success": False,
    "message": "Page not found"
  }

  return result