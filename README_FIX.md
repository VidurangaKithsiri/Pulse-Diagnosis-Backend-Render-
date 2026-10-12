# Normal / Abnormal research pulse-pattern model
Training source: ../training/train_model.py and ../training/model_training.ipynb.
Raw S1 and real MAX30102 source recordings are included in training/ for reproduction.
Pipeline: raw waveform -> 0.7–4 Hz third-order bandpass -> resample to 64 Hz -> five-second windows -> per-window z-score -> seven features -> Extra Trees.
Training labels: robust absolute deviations of max/min/range from TRAINING medians/MAD; training scores above the 70th percentile are Abnormal, otherwise Normal.
Labels are statistical feature-pattern categories, not disease or medical-risk diagnoses. risk_level remains Not medically assessed; pattern_level reports Lower/Higher deviation.
Model: 300 Extra Trees, max_depth=12, min_samples_leaf=2, class_weight=balanced, random_state=42. All settings/source/metrics are reproducible.
Data: one training subject S1; first 80% of each recording used for training, last 20% held out. Accuracy is agreement with heuristic labels, NOT clinical accuracy or unseen-subject accuracy.
Input: POST /api/v1/predict with x-api-key and JSON {sample_rate:64,sensor:MAX30102,samples:[raw values]}. Updated firmware/client supply this input. Old raw summary statistics cannot reconstruct filtering and are rejected.
Current endpoints retain the prior URL. Set Render API_KEY to match your existing client configuration. No Firebase or guardian modifications are included.
