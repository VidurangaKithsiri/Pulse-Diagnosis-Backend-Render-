import os
import traceback
import joblib
import numpy as np

from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load ML model
model = joblib.load("pulse_model.pkl")

# Read API key from Render Environment Variable
# Variable Name: API_KEY
# Variable Value: sm0399
API_KEY = os.environ.get("API_KEY")

print("Loaded API_KEY:", API_KEY)

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        key = request.headers.get("x-api-key")

        print("Received API Key:", key)
        print("Expected API Key:", API_KEY)

        if API_KEY is None:
            return jsonify({
                "error": "Server API key is not configured."
            }), 500

        if key != API_KEY:
            return jsonify({
                "error": "Unauthorized access"
            }), 401

        return f(*args, **kwargs)

    return decorated
