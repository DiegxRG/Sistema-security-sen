"""
Admin views for Firebase Auth user management.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from ...auth import (
    firebase_auth_required, ROLE_ADMIN,
    create_firebase_user, list_firebase_users, set_user_role, ALL_ROLES,
)


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def users_list(request):
    """List all Firebase Auth users with their roles."""
    users = list_firebase_users()
    return render(request, 'security/admin/users.html', {
        'users': users,
        'all_roles': ALL_ROLES,
    })


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def user_create(request):
    """Create a new Firebase Auth user."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        display_name = request.POST.get('displayName', '').strip()
        role = request.POST.get('role', 'operator')

        if not all([email, password, display_name]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('security:admin_user_create')

        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return redirect('security:admin_user_create')

        try:
            user = create_firebase_user(email, password, display_name, role)
            messages.success(request, f'Usuario "{display_name}" creado exitosamente con rol "{role}".')
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')

        return redirect('security:admin_users')

    return render(request, 'security/admin/user_form.html', {
        'all_roles': ALL_ROLES,
    })


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def user_change_role(request, uid):
    """Change a user's role."""
    if request.method == 'POST':
        new_role = request.POST.get('role', '')

        if new_role not in ALL_ROLES:
            messages.error(request, 'Rol no válido.')
            return redirect('security:admin_users')

        try:
            set_user_role(uid, new_role)
            messages.success(request, f'Rol actualizado a "{new_role}" exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar rol: {str(e)}')

    return redirect('security:admin_users')
