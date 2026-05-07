"""
Admin CRUD views for Security Shifts.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from ...auth import firebase_auth_required, ROLE_ADMIN
from ...firebase import get_shifts_ref, doc_to_dict, query_to_list


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def shifts_list(request):
    """List all shifts."""
    shifts_ref = get_shifts_ref()
    all_shifts = query_to_list(shifts_ref.get())
    return render(request, 'security/admin/shifts.html', {'shifts': all_shifts})


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def shift_create(request):
    """Create a new shift."""
    if request.method == 'POST':
        shifts_ref = get_shifts_ref()

        name = request.POST.get('name', '').strip()
        start_time = request.POST.get('startTime', '').strip() or None
        end_time = request.POST.get('endTime', '').strip() or None
        code = request.POST.get('code', '').strip()

        if not name or not code:
            messages.error(request, 'El nombre y código del turno son obligatorios.')
            return redirect('security:admin_shift_create')

        data = {
            'code': code,
            'name': name,
            'startTime': start_time,
            'endTime': end_time,
            'isActive': True,
        }

        shifts_ref.document(code).set(data)
        messages.success(request, f'Turno "{name}" creado exitosamente.')
        return redirect('security:admin_shifts')

    return render(request, 'security/admin/shift_form.html', {'editing': False})


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def shift_edit(request, shift_id):
    """Edit an existing shift."""
    shifts_ref = get_shifts_ref()

    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'startTime': request.POST.get('startTime', '').strip() or None,
            'endTime': request.POST.get('endTime', '').strip() or None,
        }

        if not data['name']:
            messages.error(request, 'El nombre del turno es obligatorio.')
            return redirect('security:admin_shift_edit', shift_id=shift_id)

        shifts_ref.document(shift_id).update(data)
        messages.success(request, 'Turno actualizado exitosamente.')
        return redirect('security:admin_shifts')

    doc = shifts_ref.document(shift_id).get()
    shift = doc_to_dict(doc)

    if not shift:
        messages.error(request, 'Turno no encontrado.')
        return redirect('security:admin_shifts')

    return render(request, 'security/admin/shift_form.html', {
        'shift': shift,
        'editing': True,
    })


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def shift_toggle(request, shift_id):
    """Toggle shift active/inactive status."""
    shifts_ref = get_shifts_ref()
    doc = shifts_ref.document(shift_id).get()
    shift = doc_to_dict(doc)

    if shift:
        new_status = not shift.get('isActive', True)
        shifts_ref.document(shift_id).update({'isActive': new_status})
        action = 'activado' if new_status else 'desactivado'
        messages.success(request, f'Turno {action} exitosamente.')

    return redirect('security:admin_shifts')
