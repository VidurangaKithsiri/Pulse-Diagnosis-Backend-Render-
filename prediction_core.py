from pathlib import Path
import json
import math
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
MODEL = joblib.load(ROOT / "pulse_model.pkl")
FEATURES = list(joblib.load(ROOT / "feature_columns.pkl"))
DOMAIN = json.loads((ROOT / "training_domain.json").read_text())

def predict_payload(data):
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    values = {}
    for name in FEATURES:
        if name not in data:
            raise ValueError(f"Missing feature: {name}")
        if isinstance(data[name], bool):
            raise ValueError(f"{name} must be numeric")
        try:
            value = float(data[name])
        except (ValueError, TypeError):
            raise ValueError(f"{name} must be numeric") from None
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        values[name] = value
    outside = [name for name in FEATURES if not DOMAIN[name]["min"] <= values[name] <= DOMAIN[name]["max"]]
    common = {"success": True, "features": values, "risk_level": "Not assessed",
              "model": "Extra Trees", "clinical_validation": False}
    if outside:
        return {**common, "prediction_id": -1, "prediction": "Unavailable", "confidence": None,
                "status": "OUT_OF_DISTRIBUTION", "out_of_range_features": outside,
                "recommendation": "This sensor window does not match the model training domain. No reliable classification is available. Correct preprocessing and validate a sensor-compatible model."}
    row = pd.DataFrame([values], columns=FEATURES)
    label = int(MODEL.predict(row)[0])
    if label not in (0, 1):
        raise RuntimeError("Unsupported model label")
    confidence = float(max(MODEL.predict_proba(row)[0]) * 100)
    return {**common, "prediction_id": label, "prediction": {0:"Normal",1:"Abnormal"}[label],
            "confidence": round(confidence,2), "status": "RESEARCH_CLASSIFICATION",
            "recommendation": "Research feature-pattern classification only. Labels were generated from feature extremes; this output does not establish health status or medical risk."}
