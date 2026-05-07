"""
Register entry and exit views.
The operator selects a guard from a list and registers their entry or exit.
"""
import json
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..auth import firebase_auth_required, ROLE_ADMIN, ROLE_OPERATOR
from ..firebase import (
    get_logs_ref, get_personnel_ref, get_areas_ref, get_shifts_ref,
    query_to_list, doc_to_dict, EXIT_REASONS,
)


@firebase_auth_required(allowed_roles=[ROLE_ADMIN, ROLE_OPERATOR])
def register_view(request):
    """Render the entry/exit registration page."""
    personnel_ref = get_personnel_ref()
    areas_ref = get_areas_ref()
    shifts_ref = get_shifts_ref()
    logs_ref = get_logs_ref()

    # Get active personnel and sort in memory to avoid composite index requirement
    active_personnel_raw = query_to_list(
        personnel_ref.where('status', '==', 'active').get()
    )
    all_personnel = sorted(active_personnel_raw, key=lambda x: x.get('lastName', '').lower())

    # Get active areas
    all_areas = query_to_list(
        areas_ref.where('isActive', '==', True).get()
    )

    # Get active shifts
    all_shifts = query_to_list(
        shifts_ref.where('isActive', '==', True).get()
    )

    # Get personnel currently inside (have entry but no exit)
    active_logs = query_to_list(
        logs_ref.where('status', '==', 'entered').get()
    )

    # Map active personnel IDs for quick lookup
    active_personnel_ids = {log['personnelId'] for log in active_logs}

    # Enrich active logs with personnel names
    personnel_map = {p['id']: p for p in all_personnel}
    for log in active_logs:
        person = personnel_map.get(log.get('personnelId'), {})
        log['personnelName'] = f"{person.get('firstName', '?')} {person.get('lastName', '')}"
        log['cargo'] = person.get('cargo', '')

    # Personnel available for entry (not currently inside)
    available_for_entry = [p for p in all_personnel if p['id'] not in active_personnel_ids]

    context = {
        'all_personnel': all_personnel,
        'available_for_entry': available_for_entry,
        'active_logs': active_logs,
        'all_areas': all_areas,
        'all_shifts': all_shifts,
        'exit_reasons': EXIT_REASONS,
    }

    return render(request, 'security/register.html', context)


@csrf_exempt
@require_POST
def register_entry(request):
    """API endpoint to register an entry."""
    try:
        # Verify auth from session
        uid = request.session.get('firebase_uid')
        role = request.session.get('firebase_role')
        if not uid or role not in [ROLE_ADMIN, ROLE_OPERATOR]:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        body = json.loads(request.body)
        personnel_id = body.get('personnelId')
        shift_id = body.get('shiftId')

        if not personnel_id or not shift_id:
            return JsonResponse({'error': 'Datos incompletos. Se requiere personnelId y shiftId.'}, status=400)

        logs_ref = get_logs_ref()

        # BUSINESS RULE: Check if guard is already inside
        existing = list(
            logs_ref
            .where('personnelId', '==', personnel_id)
            .where('status', '==', 'entered')
            .limit(1)
            .get()
        )

        if existing:
            return JsonResponse({
                'error': 'Este guardia ya tiene una entrada activa. Debe registrar su salida primero.'
            }, status=409)

        # Create entry log
        now = datetime.now()
        log_data = {
            'personnelId': personnel_id,
            'shiftId': shift_id,
            'entryTime': now,
            'exitTime': None,
            'exitReason': None,
            'exitReasonDetail': None,
            'destinationAreaId': None,
            'operatorId': uid,
            'status': 'entered',
        }

        doc_ref = logs_ref.add(log_data)

        return JsonResponse({
            'success': True,
            'message': 'Entrada registrada correctamente.',
            'logId': doc_ref[1].id,
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def register_exit(request):
    """API endpoint to register an exit."""
    try:
        # Verify auth from session
        uid = request.session.get('firebase_uid')
        role = request.session.get('firebase_role')
        if not uid or role not in [ROLE_ADMIN, ROLE_OPERATOR]:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        body = json.loads(request.body)
        log_id = body.get('logId')
        exit_reason = body.get('exitReason')
        exit_reason_detail = body.get('exitReasonDetail', '')
        destination_area_id = body.get('destinationAreaId')

        # Validations
        if not log_id:
            return JsonResponse({'error': 'Se requiere el ID del registro.'}, status=400)
        if not exit_reason:
            return JsonResponse({'error': 'El motivo de salida es obligatorio.'}, status=400)
        if exit_reason not in EXIT_REASONS:
            return JsonResponse({'error': 'Motivo de salida no válido.'}, status=400)
        if exit_reason == 'Otro' and not exit_reason_detail.strip():
            return JsonResponse({'error': 'Cuando el motivo es "Otro", el detalle es obligatorio.'}, status=400)
        if not destination_area_id:
            return JsonResponse({'error': 'El área de destino es obligatoria.'}, status=400)

        logs_ref = get_logs_ref()

        # Get the active log
        log_doc = logs_ref.document(log_id).get()
        if not log_doc.exists:
            return JsonResponse({'error': 'Registro no encontrado.'}, status=404)

        log_data = log_doc.to_dict()

        # BUSINESS RULE: Can only close an 'entered' log
        if log_data.get('status') != 'entered':
            return JsonResponse({'error': 'Este registro ya fue cerrado.'}, status=409)

        # Update the log with exit info
        now = datetime.now()
        logs_ref.document(log_id).update({
            'exitTime': now,
            'exitReason': exit_reason,
            'exitReasonDetail': exit_reason_detail if exit_reason == 'Otro' else None,
            'destinationAreaId': destination_area_id,
            'status': 'exited',
        })

        return JsonResponse({
            'success': True,
            'message': 'Salida registrada correctamente.',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
