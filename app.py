import traceback

from flask import Flask, request, jsonify
import os
import traceback
import joblib
import numpy as np

from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load ML model
model = joblib.load("pulse_model.pkl")

API_KEY = os.environ.get("sm0399")  #secure key in production
# Read API key from Render Environment Variable
# Variable Name: API_KEY
# Variable Value: sm0399
API_KEY = os.environ.get("sm0399")

print("Loaded API_KEY:", API_KEY)

# Auth function
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

@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy"
    }), 200

        print("Received API Key:", key)
        print("Expected API Key:", API_KEY)

@app.route("/api/v1/predict", methods=["POST"])
@require_api_key
def predict():
    
    print("Headers:", request.headers)
    print("Raw Data:", request.data)
        if API_KEY is None:
            return jsonify({
                "error": "Server API key is not configured."
            }), 500

    data = request.get_json()
        if key != API_KEY:
            return jsonify({
                "error": "Unauthorized access"
            }), 401

    # 🔴 Safety check (prevents 500 crash)
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
    
    try:
        # Check whether all required fields exist
        required = ["mean", "std", "max", "min", "range", "energy"]
        return f(*args, **kwargs)

        for field in required:
            if field not in data:
                return jsonify({
                    "error": f"'{field}' is missing"
                }), 400

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
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
