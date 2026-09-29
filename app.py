import os
import hmac
from flask import Flask, jsonify, request
from prediction_core import predict_payload

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16384

@app.get("/")
def home():
    return jsonify(message="Pulse Diagnosis Backend", status="Running")

@app.get("/api/v1/health")
def health():
    return jsonify(success=True, status="Healthy", model="Extra Trees", version="3.0",
                   clinical_validation=False, domain_guard=True)

@app.post("/api/v1/predict")
def predict():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        return jsonify(success=False, error="Server API key is missing"), 503
    if not hmac.compare_digest(request.headers.get("x-api-key", ""), api_key):
        return jsonify(success=False, error="Unauthorized"), 401
    if not request.is_json:
        return jsonify(success=False, error="Send application/json"), 400
    data = request.get_json(silent=True)
    try:
        return jsonify(predict_payload(data)), 200
    except ValueError as error:
        return jsonify(success=False, error=str(error)), 400
    except Exception:
        app.logger.exception("Prediction failed")
        return jsonify(success=False, error="Prediction could not be completed"), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
