"""
Admin CRUD views for Security Areas.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from ...auth import firebase_auth_required, ROLE_ADMIN
from ...firebase import get_areas_ref, doc_to_dict, query_to_list


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def areas_list(request):
    """List all areas."""
    areas_ref = get_areas_ref()
    all_areas = query_to_list(areas_ref.order_by('name').get())
    return render(request, 'security/admin/areas.html', {'areas': all_areas})


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def area_create(request):
    """Create a new area."""
    if request.method == 'POST':
        areas_ref = get_areas_ref()

        data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', '').strip(),
            'isActive': True,
        }

        if not data['name']:
            messages.error(request, 'El nombre del área es obligatorio.')
            return redirect('security:admin_area_create')

        areas_ref.add(data)
        messages.success(request, f'Área "{data["name"]}" creada exitosamente.')
        return redirect('security:admin_areas')

    return render(request, 'security/admin/area_form.html', {'editing': False})


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def area_edit(request, area_id):
    """Edit an existing area."""
    areas_ref = get_areas_ref()

    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'description': request.POST.get('description', '').strip(),
        }

        if not data['name']:
            messages.error(request, 'El nombre del área es obligatorio.')
            return redirect('security:admin_area_edit', area_id=area_id)

        areas_ref.document(area_id).update(data)
        messages.success(request, 'Área actualizada exitosamente.')
        return redirect('security:admin_areas')

    doc = areas_ref.document(area_id).get()
    area = doc_to_dict(doc)

    if not area:
        messages.error(request, 'Área no encontrada.')
        return redirect('security:admin_areas')

    return render(request, 'security/admin/area_form.html', {
        'area': area,
        'editing': True,
    })


@firebase_auth_required(allowed_roles=[ROLE_ADMIN])
def area_toggle(request, area_id):
    """Toggle area active/inactive status."""
    areas_ref = get_areas_ref()
    doc = areas_ref.document(area_id).get()
    area = doc_to_dict(doc)

    if area:
        new_status = not area.get('isActive', True)
        areas_ref.document(area_id).update({'isActive': new_status})
        action = 'activada' if new_status else 'desactivada'
        messages.success(request, f'Área {action} exitosamente.')

    return redirect('security:admin_areas')
