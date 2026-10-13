import json
import logging
import os
import smtplib
import time
from email.message import EmailMessage

import firebase_admin
from firebase_admin import auth, credentials, db

LOG = logging.getLogger(__name__)


def initialize_firebase():
    if not firebase_admin._apps:
        service_account = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT_JSON'])
        firebase_admin.initialize_app(
            credentials.Certificate(service_account),
            {'databaseURL': os.environ['FIREBASE_DATABASE_URL']},
        )


def authenticated_uid(header):
    if not header or not header.startswith('Bearer '):
        raise ValueError('Firebase ID token required')
    initialize_firebase()
    return auth.verify_id_token(header[7:].strip(), check_revoked=True)['uid']


def _email(to, patient_name, prediction):
    msg = EmailMessage()
    msg['From'] = os.environ['SMTP_USER']
    msg['To'] = to
    msg['Subject'] = 'Pulse Monitor: Abnormal Diagnosis Alert'
    msg.set_content(
        f'Pulse Monitoring System\n\nPatient: {patient_name}\n'
        f'Diagnosis status: {prediction}\n\n'
        'Please check on the patient. Seek medical attention if appropriate.\n'
        'This is a prototype alert, not a medical diagnosis.'
    )
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as smtp:
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(msg)


def notify_abnormal(patient_uid, prediction):
    if str(prediction).strip().lower() != 'abnormal':
        return {'attempted': 0, 'sent': 0}
    initialize_firebase()
    patient = db.reference(f'Users/{patient_uid}').get() or {}
    links = db.reference(f'GuardianLinks/{patient_uid}').get() or {}
    sent = 0
    attempted = 0
    for guardian_uid, link in links.items():
        if not isinstance(link, dict) or link.get('connected') is not True:
            continue
        guardian = db.reference(f'Users/{guardian_uid}').get() or {}
        if not (guardian.get('guardianEnabled') is True or str(guardian.get('role', '')).upper() == 'GUARDIAN'):
            continue
        email = str(guardian.get('email') or '').strip()
        if not email or '@' not in email:
            continue
        # Per-patient, per-guardian cooldown; transaction prevents concurrent sends.
        state = db.reference(f'GuardianEmailCooldown/{patient_uid}/{guardian_uid}')
        now = int(time.time() * 1000)
        cooldown_ms = 15 * 60 * 1000
        def reserve(old):
            if isinstance(old, dict) and now - int(old.get('lastAttemptMs', 0)) < cooldown_ms:
                return
            return {'lastAttemptMs': now, 'status': 'PROCESSING'}
        transaction = state.transaction(reserve, apply_locally=False)
        # Admin SDK transaction returns resulting value, not committed flag.
        if not isinstance(transaction, dict) or transaction.get('lastAttemptMs') != now:
            continue
        attempted += 1
        try:
            _email(email, str(patient.get('name') or 'Patient')[:100], prediction)
            state.update({'status': 'SENT'})
            sent += 1
        except Exception:
            LOG.exception('Guardian email delivery failed for guardian UID %s', guardian_uid)
            state.update({'status': 'FAILED'})
    return {'attempted': attempted, 'sent': sent}
