from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('status/<int:file_id>/', views.get_file_status, name='get_file_status'),
    path('api/upload/', views.upload_email, name='api_upload_email'),
    path('api/status/<int:pk>/', views.get_risk_score, name='api_risk_score'),
    path('api/check_rules/', views.check_rules_update),
    path('api/check_settings/', views.check_settings_update),
    path('settings/', views.firewall_settings, name='settings')
]