"""
Firebase Admin SDK initialization and Firestore helpers.
Centralizes all Firebase operations for the security system.
"""
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
from django.conf import settings
from pathlib import Path


def _initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    # If relative path, resolve from BASE_DIR
    if not Path(cred_path).is_absolute():
        cred_path = str(settings.BASE_DIR / cred_path)

    cred = credentials.Certificate(cred_path)
    return firebase_admin.initialize_app(cred)


# Initialize on module import
_app = _initialize_firebase()


def get_db():
    """Get Firestore client instance."""
    return firestore.client()


def get_auth():
    """Get Firebase Auth instance."""
    return firebase_auth


# ─── Collection References ────────────────────────────────────────────

def get_personnel_ref():
    """Get reference to security_personnel collection."""
    return get_db().collection('security_personnel')


def get_areas_ref():
    """Get reference to security_areas collection."""
    return get_db().collection('security_areas')


def get_shifts_ref():
    """Get reference to security_shifts collection."""
    return get_db().collection('security_shifts')


def get_logs_ref():
    """Get reference to security_logs collection."""
    return get_db().collection('security_logs')


# ─── Helper Functions ─────────────────────────────────────────────────

def doc_to_dict(doc):
    """Convert a Firestore document snapshot to a dict with its ID included."""
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None


def query_to_list(query_result):
    """Convert Firestore query results to a list of dicts with IDs."""
    results = []
    for doc in query_result:
        data = doc.to_dict()
        data['id'] = doc.id
        results.append(data)
    return results


# ─── Seed Default Shifts ──────────────────────────────────────────────

DEFAULT_SHIFTS = [
    {
        'code': 'T-01',
        'name': 'Mañana',
        'startTime': '06:00',
        'endTime': '14:00',
        'isActive': True,
    },
    {
        'code': 'T-02',
        'name': 'Tarde',
        'startTime': '14:00',
        'endTime': '22:00',
        'isActive': True,
    },
    {
        'code': 'T-03',
        'name': 'Noche',
        'startTime': '22:00',
        'endTime': '06:00',
        'isActive': True,
    },
    {
        'code': 'T-04',
        'name': 'Personalizado',
        'startTime': None,
        'endTime': None,
        'isActive': True,
    },
]


def seed_shifts():
    """Create default shifts in Firestore if they don't exist yet."""
    shifts_ref = get_shifts_ref()
    for shift in DEFAULT_SHIFTS:
        code = shift['code']
        # Check if shift with this code already exists
        existing = shifts_ref.where('code', '==', code).limit(1).get()
        if not list(existing):
            shifts_ref.document(code).set(shift)
            print(f"  ✅ Turno '{shift['name']}' creado con código {code}")
        else:
            print(f"  ⏭️  Turno '{shift['name']}' ya existe")


# ─── Predefined Exit Reasons ─────────────────────────────────────────

EXIT_REASONS = [
    'Ronda de vigilancia',
    'Hora de almuerzo / refrigerio',
    'Fin de turno',
    'Emergencia',
    'Permiso especial',
    'Otro',
]
