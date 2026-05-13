"""
urls.py - URL routing for the polls application.

Each URL pattern maps one URL to exactly one view function.
Organized by section: Auth, Public, Creator, Participation, Results, Export, Actions.
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── Public / Home ──────────────────────────────────────
    path('', views.home_view, name='home'),

    # ── Authentication ─────────────────────────────────────
    path('register/', views.register_view, name='register'),

    # ── Creator Dashboard ──────────────────────────────────
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # ── Poll Creation ──────────────────────────────────────
    path('create/', views.create_poll, name='create_poll'),

    # ── Poll Management ────────────────────────────────────
    path('poll/<int:poll_id>/delete/', views.delete_poll, name='delete_poll'),
    path('poll/<int:poll_id>/toggle/', views.toggle_poll_active, name='toggle_poll_active'),
    path('poll/<int:poll_id>/share/', views.poll_share, name='poll_share'),

    # ── Poll Participation ─────────────────────────────────
    path('poll/<int:poll_id>/', views.take_poll, name='take_poll'),

    # ── Results & Statistics ───────────────────────────────
    path('poll/<int:poll_id>/results/', views.poll_results, name='poll_results'),

    # ── Data Export ────────────────────────────────────────
    path('poll/<int:poll_id>/export/csv/', views.export_responses_csv, name='export_responses'),

    # ── Notifications ──────────────────────────────────────
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),

]
