from flask import Flask, request, jsonify
import os
import joblib
import numpy as np
import sqlite3
from functools import wraps

app = Flask(__name__)

model = joblib.load("pulse_model.pkl")

def new_func():
    API_KEY = os.environ.get("API_KEY","sm0399")
    return API_KEY

API_KEY = new_func()  #secure key in production

# Auth function
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")

        if key and key == API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Unauthorized access"}), 401

    return decorated

@app.route("/", methods=["GET"])
def home():
    return "Pulse Diagnosis API is running"

@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    }), 200

@app.route("/api/v1/predict", methods=["POST"])
@require_api_key
def predict():

    data = request.get_json()
    
    print("Received JSON:", data)


    # 🔴 Safety check (prevents 500 crash)
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
    
    try:
        # Check whether all required fields exist
        required = ["mean", "std", "max", "min", "range", "energy"]

        for field in required:
            if field not in data:
                return jsonify({
                    "error": f"'{field}' is missing"
                }), 400

        # Convert values to float
        features = [
            float(data["mean"]),
            float(data["std"]),
            float(data["max"]),
            float(data["min"]),
            float(data["range"]),
            float(data["energy"])
        ]

        features = np.array(features).reshape(1, -1)

        prediction = model.predict(features)[0]

        if prediction == 0:
            status = "Normal"
            risk = "Low"
        else:
            status = "Abnormal"
            risk = "High"

        return jsonify({
            "status": status,
            "risk_level": risk
        })

    except ValueError:
        return jsonify({
            "error": "All feature values must be numeric."
        }), 400

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000))
    )
