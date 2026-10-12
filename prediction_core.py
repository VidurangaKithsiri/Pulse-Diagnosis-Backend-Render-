from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from ppg_pipeline import FEATURES, recording_windows
ROOT=Path(__file__).resolve().parent
MODEL=joblib.load(ROOT/'pulse_model.pkl')
META=json.loads((ROOT/'model_metadata.json').read_text())

def predict_payload(data):
    if not isinstance(data,dict):raise ValueError('JSON body must be an object')
    if 'samples' in data:
        samples=data['samples'];fs=data.get('sample_rate')
        if not isinstance(samples,list) or not 320<=len(samples)<=8192:raise ValueError('Send 320–8192 raw waveform samples')
        if isinstance(fs,bool) or not isinstance(fs,(float,int)) or not 16<=fs<=256:raise ValueError('Invalid sample_rate')
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in samples):raise ValueError('Samples must be numeric')
        raw=np.asarray(samples,dtype=np.float64)
        if not np.isfinite(raw).all():raise ValueError('Non-finite sensor samples')
        # MAX30102 raw IR has finger-detection values above the existing firmware threshold.
        if data.get('sensor')=='MAX30102' and np.mean(raw<50000)>0.02:raise ValueError('Finger absent or unstable during capture; repeat with steady finger contact')
        rows,rejected=recording_windows(raw,float(fs),'LIVE','LIVE')
        if not rows:raise ValueError('No usable five-second pulse windows')
        X=pd.DataFrame(rows)[FEATURES]
    else:
        # The existing manual feature form can submit only features from the new pipeline.
        if any(k not in data for k in FEATURES):raise ValueError('Raw samples required. Update ESP32 firmware and Android files together.')
        values={k:float(data[k]) for k in FEATURES}
        if not all(np.isfinite(v) for v in values.values()):raise ValueError('Non-finite features')
        if abs(values['mean'])>0.001 or abs(values['std']-1)>0.001 or abs(values['variance']-1)>0.001 or abs(values['energy']-320)>0.1:
            raise ValueError('These are old raw summary features. Updated live capture sends raw samples; manual input must use the rebuilt normalized features.')
        X=pd.DataFrame([values],columns=FEATURES);rejected=0
    probabilities=MODEL.predict_proba(X)
    class_position=int(np.flatnonzero(MODEL.classes_==1)[0])
    abnormal_probability=float(probabilities[:,class_position].mean())
    label=int(abnormal_probability>=0.5)
    confidence=(abnormal_probability if label else 1-abnormal_probability)*100
    return {'success':True,'prediction_id':label,'prediction':['Normal','Abnormal'][label],
      'risk_level':'Not medically assessed','pattern_level':'Higher deviation' if label else 'Lower deviation',
      'confidence':round(confidence,2),'status':'RESEARCH_CLASSIFICATION','model':'Extra Trees',
      'pipeline_version':META['pipeline_version'],'clinical_validation':False,'window_count':len(X),'rejected_windows':rejected,
      'features':{k:float(X.iloc[-1][k]) for k in FEATURES},
      'recommendation':'Research pulse-pattern classification for project demonstration. Normal/Abnormal labels represent feature deviation, not a medical diagnosis or validated medical risk.'}
