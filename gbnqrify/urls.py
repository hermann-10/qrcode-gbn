from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register_employee, name='register_employee'),
    # Add more routes as needed
    path('scan/', views.scan_qr, name='scan'),
]
