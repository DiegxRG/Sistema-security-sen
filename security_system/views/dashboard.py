"""
Dashboard view — real-time stats of the current day.
Shows: guards currently inside, total entries/exits today, alerts for extended shifts.
"""
from datetime import datetime, timedelta
from django.shortcuts import render
from django.utils import timezone
from ..auth import firebase_auth_required
from ..firebase import get_logs_ref, get_personnel_ref, query_to_list


@firebase_auth_required()
def dashboard_view(request):
    """Main dashboard with today's statistics."""
    logs_ref = get_logs_ref()
    personnel_ref = get_personnel_ref()

    # Get all currently "entered" (inside) personnel
    active_logs = query_to_list(
        logs_ref.where('status', '==', 'entered').get()
    )

    # Get today's completed logs
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = query_to_list(
        logs_ref.where('entryTime', '>=', today_start).get()
    )

    # Get all active personnel for reference
    all_personnel = query_to_list(
        personnel_ref.where('status', '==', 'active').get()
    )
    personnel_map = {p['id']: p for p in all_personnel}

    # Enrich active logs with personnel names
    for log in active_logs:
        person = personnel_map.get(log.get('personnelId'), {})
        log['personnelName'] = f"{person.get('firstName', '?')} {person.get('lastName', '')}"
        log['cargo'] = person.get('cargo', '')
        # Calculate hours active
        entry_time = log.get('entryTime')
        if entry_time:
            if hasattr(entry_time, 'timestamp'):
                entry_dt = entry_time
            else:
                entry_dt = datetime.fromisoformat(str(entry_time))
            hours_active = (datetime.now() - entry_dt.replace(tzinfo=None)).total_seconds() / 3600
            log['hoursActive'] = round(hours_active, 1)
            log['isOvertime'] = hours_active > 9
        else:
            log['hoursActive'] = 0
            log['isOvertime'] = False

    # Stats
    total_entries_today = len(today_logs)
    total_exits_today = len([l for l in today_logs if l.get('status') == 'exited'])
    currently_inside = len(active_logs)
    overtime_alerts = len([l for l in active_logs if l.get('isOvertime', False)])

    context = {
        'active_logs': active_logs,
        'total_entries_today': total_entries_today,
        'total_exits_today': total_exits_today,
        'currently_inside': currently_inside,
        'total_personnel': len(all_personnel),
        'overtime_alerts': overtime_alerts,
    }

    return render(request, 'security/dashboard.html', context)
