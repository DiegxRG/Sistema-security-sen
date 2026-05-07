"""
Admin CRUD views for Security Personnel.
"""
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from ...auth import firebase_auth_required, ROLE_ADMIN
from ...firebase import get_personnel_ref, get_shifts_ref, doc_to_dict, query_to_list


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def personnel_list(request):
    """List all security personnel."""
    personnel_ref = get_personnel_ref()
    shifts_ref = get_shifts_ref()

    all_personnel = query_to_list(
        personnel_ref.order_by('lastName').get()
    )
    all_shifts = query_to_list(shifts_ref.get())
    shifts_map = {s['id']: s for s in all_shifts}

    # Enrich with shift names
    for person in all_personnel:
        shift = shifts_map.get(person.get('assignedShift'), {})
        person['shiftName'] = shift.get('name', '—')

    context = {
        'personnel': all_personnel,
        'all_shifts': all_shifts,
    }
    return render(request, 'security/admin/personnel.html', context)


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def personnel_create(request):
    """Create a new guard."""
    if request.method == 'POST':
        personnel_ref = get_personnel_ref()

        data = {
            'firstName': request.POST.get('firstName', '').strip(),
            'lastName': request.POST.get('lastName', '').strip(),
            'documentId': request.POST.get('documentId', '').strip(),
            'cargo': request.POST.get('cargo', '').strip(),
            'assignedShift': request.POST.get('assignedShift', 'T-01'),
            'status': 'active',
            'createdAt': datetime.now(),
        }

        # Validations
        if not all([data['firstName'], data['lastName'], data['documentId'], data['cargo']]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('security:admin_personnel_create')

        # Check if DNI already exists
        existing = list(
            personnel_ref.where('documentId', '==', data['documentId']).limit(1).get()
        )
        if existing:
            messages.error(request, f'Ya existe un guardia con DNI {data["documentId"]}.')
            return redirect('security:admin_personnel_create')

        personnel_ref.add(data)
        messages.success(request, f'Guardia {data["firstName"]} {data["lastName"]} creado exitosamente.')
        return redirect('security:admin_personnel')

    # GET — render form
    all_shifts = query_to_list(get_shifts_ref().where('isActive', '==', True).get())
    return render(request, 'security/admin/personnel_form.html', {
        'all_shifts': all_shifts,
        'editing': False,
    })


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def personnel_edit(request, personnel_id):
    """Edit an existing guard."""
    personnel_ref = get_personnel_ref()

    if request.method == 'POST':
        data = {
            'firstName': request.POST.get('firstName', '').strip(),
            'lastName': request.POST.get('lastName', '').strip(),
            'documentId': request.POST.get('documentId', '').strip(),
            'cargo': request.POST.get('cargo', '').strip(),
            'assignedShift': request.POST.get('assignedShift', 'T-01'),
        }

        if not all([data['firstName'], data['lastName'], data['documentId'], data['cargo']]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('security:admin_personnel_edit', personnel_id=personnel_id)

        personnel_ref.document(personnel_id).update(data)
        messages.success(request, 'Guardia actualizado exitosamente.')
        return redirect('security:admin_personnel')

    # GET — load existing data
    doc = personnel_ref.document(personnel_id).get()
    person = doc_to_dict(doc)

    if not person:
        messages.error(request, 'Guardia no encontrado.')
        return redirect('security:admin_personnel')

    all_shifts = query_to_list(get_shifts_ref().where('isActive', '==', True).get())
    return render(request, 'security/admin/personnel_form.html', {
        'person': person,
        'all_shifts': all_shifts,
        'editing': True,
    })


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def personnel_toggle(request, personnel_id):
    """Toggle guard active/inactive status."""
    personnel_ref = get_personnel_ref()
    doc = personnel_ref.document(personnel_id).get()
    person = doc_to_dict(doc)

    if person:
        new_status = 'inactive' if person.get('status') == 'active' else 'active'
        personnel_ref.document(personnel_id).update({'status': new_status})
        action = 'activado' if new_status == 'active' else 'desactivado'
        messages.success(request, f'Guardia {action} exitosamente.')

    return redirect('security:admin_personnel')
