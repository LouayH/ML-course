import sys
import threading
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods = ["GET"])
def index():
  return ('', 204)

@app.errorhandler(404)
def notFound(error):
  result = {
    "success": False,
    "message": "Page not found"
  }

  return result