"""
URL configuration for easycert_django project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django built-in admin
    path("admin/",     admin.site.urls),

    # Accounts (login, register, logout)
    path("accounts/",  include("apps.accounts.urls")),

    # Home + Certificates + Admin Dashboard
    path("",           include("apps.requests_app.urls")),
]
