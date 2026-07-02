import traceback

from flask import Flask, request, jsonify
import os
import joblib
import numpy as np
from functools import wraps

app = Flask(__name__)

# Load ML model
model = joblib.load("pulse_model.pkl")

# API Key from Render Environment Variables
def new_func():
    API_KEY = os.environ.get("API_KEY","sm0399")
    return API_KEY

API_KEY = new_func()

if API_KEY is None:
    raise ValueError("API_KEY environment variable is not set.")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        key = request.headers.get("x-api-key")

        if key == API_KEY:
            return f(*args, **kwargs)

        return jsonify({
            "error": "Unauthorized access"
        }), 401

    return decorated

@app.route("/", methods=["GET"])
def home():
    return "Pulse Diagnosis API is running"


#@app.route("/api/v1/health", methods=["GET"])
#def health():
#
#    return jsonify({
#        "status": "healthy"
#    }), 200


@app.route("/api/v1/predict", methods=["POST"])
@require_api_key
def predict():
    
    print("Headers:", request.headers)
    print("Raw Data:", request.data)

    data = request.get_json()
    
    print("Received JSON:", data)

    if not data:
        return jsonify({
            "error": "No JSON data received"
        }), 400
        
    
    try:

        required = [
            "mean",
            "std",
            "variance",
            "min",
            "max",
            "energy",
        ]

        for field in required:
            if field not in data:
                return jsonify({
                    "error": f"'{field}' is missing"
                }), 400

        features = [
            float(data["mean"]),
            float(data["std"]),
            float(data["variance"]),
            float(data["min"]),
            float(data["max"]),
            float(data["energy"]),
        ]

        features = np.array(features).reshape(1, -1)

        prediction = int(model.predict(features)[0])

        if prediction == 0:
            status = "Normal"
            risk = "Low"
        else:
            status = "Abnormal"
            risk = "High"

        return jsonify({
            "prediction": prediction,
            "status": status,
            "risk_level": risk
        })

    except ValueError:
        return jsonify({
            "error": "All feature values must be numeric."
        }), 400

    except Exception as e:
        print("ERROR:", str(e))
        traceback.print_exc()

        return jsonify({
        "error": str(e)
        }), 400
        

    

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000))
    )
