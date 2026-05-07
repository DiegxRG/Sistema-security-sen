"""
Context processors for passing data to all templates.
"""
import json
from django.conf import settings


def firebase_config(request):
    """
    Make Firebase Web SDK config available in all templates.
    Also passes the current user info if authenticated.
    """
    firebase_user = getattr(request, 'firebase_user', None)

    return {
        'firebase_config': json.dumps(settings.FIREBASE_WEB_CONFIG),
        'firebase_user': firebase_user,
        'user_role': firebase_user['role'] if firebase_user else None,
        'is_admin': firebase_user['role'] == 'admin' if firebase_user else False,
        'is_operator': firebase_user['role'] in ('admin', 'operator') if firebase_user else False,
        'is_supervisor': firebase_user['role'] in ('admin', 'supervisor') if firebase_user else False,
    }
