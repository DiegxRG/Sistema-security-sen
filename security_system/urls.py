"""
URL configuration for the security_system app.
"""
from django.urls import path
from .views import dashboard, register, logs, reports, auth_views
from .views.admin import personnel, areas, shifts, users

app_name = 'security'

urlpatterns = [
    # ─── Authentication ───────────────────────────────────────
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('api/session/', auth_views.create_session, name='create_session'),

    # ─── Dashboard ────────────────────────────────────────────
    path('', dashboard.dashboard_view, name='dashboard'),

    # ─── Register Entry/Exit ──────────────────────────────────
    path('register/', register.register_view, name='register'),
    path('api/entry/', register.register_entry, name='api_entry'),
    path('api/exit/', register.register_exit, name='api_exit'),

    # ─── Logs / History ───────────────────────────────────────
    path('logs/', logs.logs_view, name='logs'),

    # ─── Reports ──────────────────────────────────────────────
    path('reports/', reports.reports_view, name='reports'),
    path('reports/export/excel/', reports.export_excel, name='export_excel'),
    path('reports/export/pdf/', reports.export_pdf, name='export_pdf'),

    # ─── Admin: Personnel ─────────────────────────────────────
    path('admin/personnel/', personnel.personnel_list, name='admin_personnel'),
    path('admin/personnel/create/', personnel.personnel_create, name='admin_personnel_create'),
    path('admin/personnel/<str:personnel_id>/edit/', personnel.personnel_edit, name='admin_personnel_edit'),
    path('admin/personnel/<str:personnel_id>/toggle/', personnel.personnel_toggle, name='admin_personnel_toggle'),

    # ─── Admin: Areas ─────────────────────────────────────────
    path('admin/areas/', areas.areas_list, name='admin_areas'),
    path('admin/areas/create/', areas.area_create, name='admin_area_create'),
    path('admin/areas/<str:area_id>/edit/', areas.area_edit, name='admin_area_edit'),
    path('admin/areas/<str:area_id>/toggle/', areas.area_toggle, name='admin_area_toggle'),

    # ─── Admin: Shifts ────────────────────────────────────────
    path('admin/shifts/', shifts.shifts_list, name='admin_shifts'),
    path('admin/shifts/create/', shifts.shift_create, name='admin_shift_create'),
    path('admin/shifts/<str:shift_id>/edit/', shifts.shift_edit, name='admin_shift_edit'),
    path('admin/shifts/<str:shift_id>/toggle/', shifts.shift_toggle, name='admin_shift_toggle'),

    # ─── Admin: Users ─────────────────────────────────────────
    path('admin/users/', users.users_list, name='admin_users'),
    path('admin/users/create/', users.user_create, name='admin_user_create'),
    path('admin/users/<str:uid>/role/', users.user_change_role, name='admin_user_role'),
]
