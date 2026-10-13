import hmac
import os
from flask import Flask, jsonify, request
from prediction_core import predict_payload
from guardian_email import authenticated_uid, notify_abnormal

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024

@app.get('/')
def home():
    return jsonify(message='Pulse Diagnosis Backend', status='Running', version='4.0-research-raw')

@app.get('/favicon.ico')
def favicon():
    return '', 204

@app.get('/api/v1/health')
def health():
    return jsonify(success=True, status='Healthy', version='4.0-research-raw',
                   pipeline_version='ppg-window-v1', input='raw samples + sample_rate',
                   prediction_labels=['Normal', 'Abnormal'], clinical_validation=False)

@app.post('/api/v1/predict')
def predict():
    expected = os.environ.get('API_KEY')
    if not expected:
        return jsonify(success=False, error='Server API_KEY is missing'), 503
    if not hmac.compare_digest(request.headers.get('x-api-key', ''), expected):
        return jsonify(success=False, error='Unauthorized'), 401
    if not request.is_json:
        return jsonify(success=False, error='Send application/json'), 400
    try:
        patient_uid = authenticated_uid(request.headers.get('Authorization', ''))
    except Exception:
        return jsonify(success=False, error='Invalid or missing Firebase login token'), 401
    try:
        result = predict_payload(request.get_json(silent=True))
        if isinstance(result, dict) and str(result.get('prediction', '')).strip().lower() == 'abnormal':
            try:
                notify_abnormal(patient_uid, result['prediction'])
            except Exception:
                app.logger.exception('Guardian email notification failed; prediction remains valid')
        return jsonify(result), 200
    except (ValueError, TypeError) as error:
        return jsonify(success=False, error=str(error)), 400
    except Exception:
        app.logger.exception('Prediction failed')
        return jsonify(success=False, error='Prediction failed; check server logs'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
