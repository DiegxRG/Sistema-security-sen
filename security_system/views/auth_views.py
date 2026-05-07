"""
Authentication views: Login, Logout, Session management.
Firebase Auth is handled client-side (JS). Once the user signs in,
the ID token is sent to this endpoint to create a server-side session.
"""
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from ..auth import verify_firebase_token, get_user_role


def login_view(request):
    """Render the login page with Firebase Auth UI."""
    # If already logged in, redirect to dashboard
    if request.session.get('firebase_token'):
        return redirect('security:dashboard')
    return render(request, 'security/login.html')


def logout_view(request):
    """Clear session and redirect to login."""
    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('security:login')


@csrf_exempt
@require_POST
def create_session(request):
    """
    API endpoint called by the frontend JS after Firebase Auth sign-in.
    Receives the ID token, verifies it, and stores it in the Django session.
    """
    try:
        body = json.loads(request.body)
        id_token = body.get('idToken')

        if not id_token:
            return JsonResponse({'error': 'Token no proporcionado'}, status=400)

        # Verify the token
        decoded = verify_firebase_token(id_token)
        if not decoded:
            return JsonResponse({'error': 'Token inválido'}, status=401)

        # Get role
        role = get_user_role(decoded)

        # Store in session
        request.session['firebase_token'] = id_token
        request.session['firebase_uid'] = decoded['uid']
        request.session['firebase_email'] = decoded.get('email', '')
        request.session['firebase_role'] = role
        request.session['firebase_name'] = decoded.get('name', decoded.get('email', ''))

        return JsonResponse({
            'success': True,
            'role': role,
            'redirect': '/security/',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
