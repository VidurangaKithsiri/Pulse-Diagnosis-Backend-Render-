"""Correct loaders and common PPG window features. Does not invent health labels."""
from pathlib import Path
import csv
import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt, resample_poly
from fractions import Fraction
FEATURES = ['mean', 'std', 'variance', 'max', 'min', 'range', 'energy']
TARGET_FS = 64
WINDOW_SECONDS = 5

def read_bvp(path):
    values = pd.read_csv(path, header=None).iloc[:,0].to_numpy(dtype=np.float64)
    if len(values) < 3: raise ValueError('BVP file is too short')
    timestamp, fs = float(values[0]), float(values[1])
    if not np.isfinite(timestamp) or timestamp < 100000000 or not 16 <= fs <= 1000:
        raise ValueError('Expected timestamp on row 1 and sampling rate on row 2')
    signal = values[2:]
    if not np.isfinite(signal).all(): raise ValueError('Non-finite BVP samples')
    return signal, fs

def read_sensor_log(path):
    rows = []; header_seen = False; sessions = []; ignored = 0
    with open(path, newline='', encoding='utf-8-sig') as stream:
        for fields in csv.reader(stream):
            if fields[:4] == ['Timestamp', 'IR', 'BPM', 'AvgBPM']:
                if rows: sessions.append(rows); rows=[]
                header_seen = True; continue
            if not header_seen or len(fields) != 4: ignored += 1; continue
            try:
                values = [float(x) for x in fields]
                if not np.isfinite(values).all(): raise ValueError()
            except ValueError: ignored += 1; continue
            if rows and values[0] <= rows[-1][0]: sessions.append(rows); rows=[]
            rows.append(values)
    if rows: sessions.append(rows)
    if not sessions: raise ValueError('No valid sensor rows found after Timestamp,IR,BPM,AvgBPM header')
    return sessions, ignored

def window_features(samples, source_fs):
    """Same function must be used for training AND raw-waveform live inference."""
    raw = np.asarray(samples, dtype=np.float64)
    n = round(source_fs * WINDOW_SECONDS)
    if len(raw) != n or not np.isfinite(raw).all(): raise ValueError('Window length/values invalid')
    raw = raw - raw.mean()
    if raw.std() < 1e-8: raise ValueError('Flat/no-signal window')
    sos = butter(3, [0.7,4.0], btype='bandpass', fs=source_fs, output='sos')
    filtered = sosfiltfilt(sos, raw)
    ratio = Fraction(TARGET_FS / source_fs).limit_denominator(10000)
    filtered = resample_poly(filtered, ratio.numerator, ratio.denominator)
    target_n = TARGET_FS * WINDOW_SECONDS
    if len(filtered) < target_n: raise ValueError('Resampling produced a short window')
    filtered = filtered[:target_n]
    scale = filtered.std()
    if scale < 1e-8: raise ValueError('No usable filtered signal')
    normalized = (filtered-filtered.mean()) / scale
    return {'mean':float(normalized.mean()),'std':float(normalized.std()),'variance':float(normalized.var()),
        'max':float(normalized.max()),'min':float(normalized.min()),'range':float(np.ptp(normalized)),
        'energy':float(np.sum(normalized*normalized))}

def recording_windows(signal, fs, subject, recording, skip_seconds=0):
    n=round(fs*WINDOW_SECONDS); rows=[]; rejected=0
    for start in range(round(fs*skip_seconds),len(signal)-n+1,n):
        try: features=window_features(signal[start:start+n],fs)
        except ValueError: rejected+=1;continue
        rows.append({'subject':subject,'recording':recording,'window_start_s':start/fs,**features})
    return rows,rejected

def sensor_windows(session, subject='MAX30102', recording='sensor'):
    values=np.asarray(session,dtype=np.float64); seconds=values[:,0]/1000
    step=float(np.median(np.diff(seconds)))
    if not 0<step<=0.0625: raise ValueError('Sensor timestamps cannot establish a usable sample rate')
    # Uniform 64 Hz grid per window; reject finger-absent and long-gap windows.
    rows=[]; rejected=0
    for start in np.arange(seconds[0],seconds[-1]-WINDOW_SECONDS,WINDOW_SECONDS):
        selected=(seconds>=start)&(seconds<start+WINDOW_SECONDS)
        part=values[selected];times=seconds[selected]
        if len(part)<32 or np.any(part[:,1]<50000) or np.max(np.diff(times))>0.15:
            rejected+=1;continue
        grid=start+np.arange(TARGET_FS*WINDOW_SECONDS)/TARGET_FS
        if times[-1]<grid[-1]-step: rejected+=1;continue
        raw=np.interp(grid,seconds,values[:,1])
        try: features=window_features(raw,TARGET_FS)
        except ValueError: rejected+=1;continue
        rows.append({'subject':subject,'recording':recording,'window_start_s':float(start),**features})
    return rows,rejected
