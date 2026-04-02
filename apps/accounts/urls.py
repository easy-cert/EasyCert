from django.urls import path
from . import views

urlpatterns = [
    path("login/",              views.login_view,              name="login"),
    path("register/",           views.register_view,           name="register"),
    path("logout/",             views.logout_view,             name="logout"),
    path("select-barangay/",    views.select_barangay_view,    name="select_barangay"),
    path("membership-pending/", views.membership_pending_view, name="membership_pending"),
    path("dashboard/",          views.user_dashboard_view,     name="user_dashboard"),
    path("settings/",           views.profile_settings_view,   name="profile_settings"),
    
    # Security Features
    path("verify-otp/",         views.verify_otp_view,         name="verify_otp"),
    path("verify-device/<uuid:token>/", views.verify_new_device_view, name="verify_new_device"),
    
    # API Endpoints
    path("api/notifications/clear/", views.clear_notifications_api, name="clear_notifications"),
    path("api/notifications/mark-read/", views.mark_notifications_read_api, name="mark_notifications_read"),
    path("api/notifications/count/", views.get_notification_count_api, name="get_notification_count"),

    # Super Admin: Barangay Admin Management
    path("super-admin/", views.superadmin_dashboard_view, name="superadmin_dashboard"),
    path("super-admin/register/", views.register_admin_view, name="register_admin"),
    path("super-admin/edit/<int:pk>/", views.edit_admin_view, name="edit_admin"),
    path("super-admin/delete/<int:pk>/", views.delete_admin_view, name="delete_admin"),
    path("super-admin/toggle-active/<int:pk>/", views.toggle_admin_active_view, name="toggle_admin_active"),
    path("super-admin/reset-pin/<int:pk>/", views.reset_admin_pin_view, name="reset_admin_pin"),
]
