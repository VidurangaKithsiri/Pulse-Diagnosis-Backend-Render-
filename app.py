import os
import traceback
from functools import wraps

import joblib
import numpy as np

from functools import wraps
from flask import Flask, request, jsonify
from flask import Flask, jsonify, request

app = Flask(__name__)

# Load ML model
# -----------------------------
# Load ML Model
# -----------------------------
model = joblib.load("pulse_model.pkl")

# Read API key from Render Environment Variable
# Variable Name: API_KEY
# Variable Value: sm0399
API_KEY = os.environ.get("API_KEY")
# -----------------------------
# API Key
# Render Environment Variable:
# Name : API_KEY
# Value: sm0399
# -----------------------------
API_KEY = os.environ.get("API_KEY", "sm0399")

print("=" * 50)
print("Pulse Diagnosis API Starting...")
print("Loaded API_KEY:", API_KEY)
print("=" * 50)


# -----------------------------
# API Key Authentication
# -----------------------------
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
@@ -27,11 +39,6 @@ def decorated(*args, **kwargs):
        print("Received API Key:", key)
        print("Expected API Key:", API_KEY)

        if API_KEY is None:
            return jsonify({
                "error": "Server API key is not configured."
            }), 500

        if key != API_KEY:
            return jsonify({
                "error": "Unauthorized access"
@@ -40,3 +47,108 @@ def decorated(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated


# -----------------------------
# Home
# -----------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Pulse Diagnosis API is running"
    }), 200


# -----------------------------
# Health Check
# -----------------------------
@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    }), 200


# -----------------------------
# Prediction Endpoint
# -----------------------------
@app.route("/api/v1/predict", methods=["POST"])
@require_api_key
def predict():

    try:

        print("Headers:", dict(request.headers))

        data = request.get_json()

        print("Received JSON:", data)

        if not data:
            return jsonify({
                "error": "No JSON data received"
            }), 400

        required = [
            "mean",
            "std",
            "min",
            "max",
            "range",
            "energy"
        ]

        for field in required:
            if field not in data:
                return jsonify({
                    "error": f"'{field}' is missing"
                }), 400

        features = np.array([
            float(data["mean"]),
            float(data["std"]),
            float(data["min"]),
            float(data["max"]),
            float(data["range"]),
            float(data["energy"])
        ]).reshape(1, -1)

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
        }), 200

    except ValueError:
        return jsonify({
            "error": "All feature values must be numeric."
        }), 400

    except Exception as e:

        print("Prediction Error:")
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# -----------------------------
# Run Local Server
# -----------------------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
