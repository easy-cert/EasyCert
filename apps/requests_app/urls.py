from django.urls import path
from . import views

urlpatterns = [
    # ── Resident pages ──
    path("",             views.home_view,           name="home"),

    # ── AJAX endpoints (resident) ──
    path("submit/",      views.submit_request_view, name="submit_request"),
    path("track/",       views.track_request_view,  name="track_request"),

    # ── Admin dashboard ──
    path("dashboard/",   views.admin_dashboard_view, name="admin_dashboard"),
    path("memberships/", views.admin_memberships_view, name="admin_memberships"),

    # ── Admin AJAX endpoints ──
    path("api/requests/",      views.admin_requests_api,   name="admin_requests_api"),
    path("api/stats/",         views.admin_stats_api,      name="admin_stats_api"),
    path("api/update/<int:pk>/", views.admin_update_status, name="admin_update_status"),

    # ── Admin Membership endpoints ──
    path("api/memberships/",           views.admin_memberships_api,      name="admin_memberships_api"),
    path("api/memberships/approve/",   views.admin_approve_membership,   name="admin_approve_membership"),
    path("api/memberships/reject/",    views.admin_reject_membership,    name="admin_reject_membership"),

    # -- Resident CRUD (Admin) --
    path("api/residents/create/",    views.admin_resident_create_api,   name="admin_resident_create"),
    path("api/residents/update/<int:pk>/", views.admin_resident_update_api, name="admin_resident_update"),
    path("api/residents/delete/<int:pk>/", views.admin_resident_delete_api, name="admin_resident_delete"),
    path("api/residents/reset-pin/<int:pk>/", views.admin_resident_reset_pin_api, name="admin_resident_reset_pin"),

    # -- Export --
    path("export/requests/", views.export_requests_csv, name="export_requests_csv"),
    path("export/residents/", views.export_residents_csv, name="export_residents_csv"),
]
