"""
Logs view — historical records with combined filters.
Read-only table showing all entry/exit events.
"""
from datetime import datetime, timedelta
from django.shortcuts import render
from ..auth import firebase_auth_required
from ..firebase import (
    get_logs_ref, get_personnel_ref, get_areas_ref, get_shifts_ref,
    query_to_list,
)


@firebase_auth_required()
def logs_view(request):
    """Display filterable history of all security logs."""
    logs_ref = get_logs_ref()
    personnel_ref = get_personnel_ref()
    areas_ref = get_areas_ref()
    shifts_ref = get_shifts_ref()

    # Get filter parameters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    personnel_id = request.GET.get('personnel_id', '')
    area_id = request.GET.get('area_id', '')
    shift_id = request.GET.get('shift_id', '')
    reason = request.GET.get('reason', '')
    status_filter = request.GET.get('status', '')

    # Build query
    query = logs_ref.order_by('entryTime', direction='DESCENDING')

    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.where('entryTime', '>=', dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            query = query.where('entryTime', '<=', dt_to)
        except ValueError:
            pass

    # Execute query
    all_logs = query_to_list(query.limit(500).get())

    # Apply client-side filters (Firestore compound queries are limited)
    if personnel_id:
        all_logs = [l for l in all_logs if l.get('personnelId') == personnel_id]
    if area_id:
        all_logs = [l for l in all_logs if l.get('destinationAreaId') == area_id]
    if shift_id:
        all_logs = [l for l in all_logs if l.get('shiftId') == shift_id]
    if reason:
        all_logs = [l for l in all_logs if l.get('exitReason') == reason]
    if status_filter:
        all_logs = [l for l in all_logs if l.get('status') == status_filter]

    # Get reference data for dropdowns and enrichment
    all_personnel = query_to_list(personnel_ref.get())
    all_areas = query_to_list(areas_ref.get())
    all_shifts = query_to_list(shifts_ref.get())

    personnel_map = {p['id']: p for p in all_personnel}
    areas_map = {a['id']: a for a in all_areas}
    shifts_map = {s['id']: s for s in all_shifts}

    # Enrich logs with readable names
    for log in all_logs:
        person = personnel_map.get(log.get('personnelId'), {})
        log['personnelName'] = f"{person.get('firstName', '?')} {person.get('lastName', '')}"
        log['personnelDni'] = person.get('documentId', '')
        log['cargo'] = person.get('cargo', '')

        area = areas_map.get(log.get('destinationAreaId'), {})
        log['areaName'] = area.get('name', '—')

        shift = shifts_map.get(log.get('shiftId'), {})
        log['shiftName'] = shift.get('name', '—')

        # Calculate duration if exited
        if log.get('exitTime') and log.get('entryTime'):
            entry = log['entryTime']
            exit_t = log['exitTime']
            if hasattr(entry, 'timestamp') and hasattr(exit_t, 'timestamp'):
                delta = exit_t - entry
                hours = delta.total_seconds() / 3600
                log['duration'] = f"{int(hours)}h {int((hours % 1) * 60)}m"
            else:
                log['duration'] = '—'
        else:
            log['duration'] = 'En curso'

    context = {
        'logs': all_logs,
        'all_personnel': all_personnel,
        'all_areas': all_areas,
        'all_shifts': all_shifts,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'personnel_id': personnel_id,
            'area_id': area_id,
            'shift_id': shift_id,
            'reason': reason,
            'status': status_filter,
        },
    }

    return render(request, 'security/logs.html', context)
