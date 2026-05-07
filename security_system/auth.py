"""
Firebase Authentication decorators and role management.
Verifies Firebase JWT tokens and custom claims for role-based access control.
"""
import functools
import json
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from .firebase import get_auth


# Role constants
ROLE_ADMIN = 'admin'
ROLE_OPERATOR = 'operator'
ROLE_SUPERVISOR = 'supervisor'
ROLE_READONLY = 'readonly'

ALL_ROLES = [ROLE_ADMIN, ROLE_OPERATOR, ROLE_SUPERVISOR, ROLE_READONLY]


def verify_firebase_token(id_token):
    """
    Verify a Firebase ID token and return the decoded claims.
    Returns None if the token is invalid.
    """
    try:
        auth = get_auth()
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def get_user_role(decoded_token):
    """Extract the role from custom claims. Defaults to 'readonly'."""
    return decoded_token.get('role', ROLE_READONLY)


def firebase_auth_required(allowed_roles=None):
    """
    Decorator that verifies Firebase Authentication.

    Usage:
        @firebase_auth_required()  # Any authenticated user
        @firebase_auth_required(allowed_roles=['admin', 'operator'])  # Specific roles only

    The Firebase ID token should be stored in the session as 'firebase_token'.
    The decoded user info is added to request as request.firebase_user.
    """
    if allowed_roles is None:
        allowed_roles = ALL_ROLES

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get token from session
            id_token = request.session.get('firebase_token')

            if not id_token:
                # No token — redirect to login
                messages.warning(request, 'Debes iniciar sesión para acceder.')
                return redirect('security:login')

            # Verify token
            decoded = verify_firebase_token(id_token)
            if not decoded:
                # Invalid/expired token — clear session and redirect
                request.session.flush()
                messages.error(request, 'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.')
                return redirect('security:login')

            # Check role
            user_role = get_user_role(decoded)
            if user_role not in allowed_roles:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('security:dashboard')

            # Attach user info to request
            request.firebase_user = {
                'uid': decoded['uid'],
                'email': decoded.get('email', ''),
                'role': user_role,
                'name': decoded.get('name', decoded.get('email', 'Usuario')),
            }

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def set_user_role(uid, role):
    """
    Set custom claims (role) for a Firebase user.
    Only admin users should call this function.
    """
    if role not in ALL_ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of {ALL_ROLES}")

    auth = get_auth()
    auth.set_custom_user_claims(uid, {'role': role})
    return True


def create_firebase_user(email, password, display_name, role=ROLE_OPERATOR):
    """
    Create a new Firebase Auth user with a role.
    Returns the created user record.
    """
    auth = get_auth()
    user = auth.create_user(
        email=email,
        password=password,
        display_name=display_name,
    )
    # Set role
    auth.set_custom_user_claims(user.uid, {'role': role})
    return user


def list_firebase_users():
    """List all Firebase Auth users with their roles."""
    auth = get_auth()
    users = []
    page = auth.list_users()
    while page:
        for user in page.users:
            claims = user.custom_claims or {}
            users.append({
                'uid': user.uid,
                'email': user.email,
                'displayName': user.display_name or '',
                'role': claims.get('role', ROLE_READONLY),
                'disabled': user.disabled,
            })
        page = page.get_next_page()
    return users
