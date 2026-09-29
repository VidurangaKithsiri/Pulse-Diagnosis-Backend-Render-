# Backend correction

Replace the backend files with this ZIP and redeploy Render. Preserve API_KEY in the Render environment; there is no hardcoded fallback key anymore. Keep the existing start command: gunicorn app:app.

Changes: validates JSON/numeric finite values, loads artifacts relative to app files, enforces API_KEY, matches model scikit-learn version (1.7.1), and checks features against the cleaned 1144-row training domain reconstructed from the supplied CSV. The original requirements.txt was UTF-16 and pinned scikit-learn 1.5.1; this file is UTF-8.

Raw MAX30102 30-second features do not match normalized 5-second training data. Out-of-domain inputs now return HTTP 200 with prediction=Unavailable, prediction_id=-1, status=OUT_OF_DISTRIBUTION, confidence=null and risk_level=Not assessed. This response prevents unsupported sensor data being called high risk. The recent history-enabled Android client displays and records the response. Older Diagnosis.java treats ID -1 as empty.

In-domain Normal/Abnormal labels are retained as research pattern labels, with risk_level=Not assessed. The original backend mapped every Abnormal output to High even though labels were created from feature deviations. No artificial Normal results or threshold changes were introduced.

Model unchanged. To make reliable sensor classifications, rebuild feature data from all subject recordings with correct timestamp/sample-rate header handling, fix the builder's segmentation indentation, use identical filtering/normalization/window lengths during training and inference, obtain independently justified labels, and validate across subjects and MAX30102 recordings. Summary features alone cannot reconstruct the original filtered waveform. The included data contains raw recordings but no verified clinical labels.

Tests: four core unittest cases passed (domain rejection, in-domain classification, invalid numbers and missing fields). Python compilation passed. Tests ran under local scikit-learn 1.8.0 with a version warning; production is pinned to the artifact version 1.7.1. Flask HTTP endpoints and deployed Render service were not exercised here because Flask was unavailable. Run pip install -r requirements.txt, then python -m unittest -v test_prediction_core, then test API requests in your deployed environment.

This fixes misleading HIGH output and API handling; it does not establish a medically valid prediction model. No remote deployment was performed.
