import os
import traceback
from functools import wraps

import joblib
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load ML model
model = joblib.load("pulse_model.pkl")

# Read API key from Render Environment Variable
# Render:
# Variable Name : API_KEY
# Variable Value: sm0399
API_KEY = os.environ.get("API_KEY")

print("Loaded API_KEY:", API_KEY)


# ==========================
# API Key Authentication
# ==========================
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


# ==========================
# Health Check
# ==========================
@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    }), 200


# ==========================
# Prediction Endpoint
# ==========================
@app.route("/api/v1/predict", methods=["POST"])
@require_api_key
def predict():

    print("Headers:", dict(request.headers))
    print("Raw Data:", request.data)

    data = request.get_json(silent=True)

    # Check JSON
    if data is None:
        return jsonify({
            "error": "No JSON data received"
        }), 400

    try:
        # Required fields
        required = [
            "mean",
            "std",
            "max",
            "min",
            "range",
            "energy"
        ]

        # Check missing fields
        for field in required:
            if field not in data:
                return jsonify({
                    "error": f"'{field}' is missing"
                }), 400

        # Convert to float
        features = [
            float(data["mean"]),
            float(data["std"]),
            float(data["max"]),
            float(data["min"]),
            float(data["range"]),
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
        }), 200

    except ValueError:
        return jsonify({
            "error": "All feature values must be numeric."
        }), 400

    except Exception as e:
        print("ERROR:", str(e))
        traceback.print_exc()

        return jsonify({
            "error": str(e)
        }), 500


# ==========================
# Run Flask App
# ==========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )