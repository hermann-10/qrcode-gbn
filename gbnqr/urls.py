from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.views.generic import RedirectView
from django.views.static import serve

from gbnqrify import views

from gbnqrify.views import attendance_clustering_view


urlpatterns = [
    # Admin & Auth
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Home - Redirect to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),


    path('', include('gbnqrify.urls')),

    # QR Scanner (User)
    path('scan/', views.scan_qr, name='scan'),
    path('ajax/check-qr/', views.check_qr_ajax, name='check_qr_ajax'),

    # Dashboard (Admin)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('filter/', views.employee_filter, name='employee_filter'),

    # Employee Management
    path('employee/register/', views.employee_register, name='employee_register'),
    path('employee/<uuid:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employee/qr/print/<uuid:employee_id>/', views.employee_qr_print, name='employee_qr_print'),
    path('employee-data/', views.employee_data, name='employee_data'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/edit/<uuid:pk>/', views.edit_employee, name='edit_employee'),
    path('employees/delete/<uuid:pk>/', views.delete_employee, name='delete_employee'),

    # Analytics
    path('analytics/dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/general/', views.general_view, name='analytics_general'),
    path('analytics/department/', views.department_analytics, name='department_analytics'),
    
    path('employee-analytics/', views.employee_analytics, name='employee_analytics'),
    
    path('analytics/employee/status-today/', views.fetch_attendance_status_today, name='fetch_attendance_status_today'),
    
    path('fetch_attendance_status_today/', views.fetch_attendance_status_today, name='fetch_attendance_status_today'),
    path('analytics/employee/', views.employee_analytics, name='employee_analytics'),
    path('analytics/employee/data/', views.fetch_employee_data, name='fetch_employee_data'),
    path('analytics/employee/download/', views.download_employee_excel, name='download_employee_excel'),
    

    # API Endpoints
    path('api/attendance/', views.get_attendance_data, name='attendance_data'),
    path('api/department-attendance/', views.department_attendance_data, name='department_attendance_data'),
    path('api/fetch-employee/', views.fetch_employee_data, name='fetch_employee_data'),
    path('fetch-employee-data/', views.fetch_employee_data, name='fetch_employee_data'),
    
    
    path('attendance-clustering/', views.attendance_clustering_view, name='attendance_clustering'),
    
    path('export-attendance-excel/', views.export_attendance_excel, name='export_attendance_excel'),
        
]

# Static files - WhiteNoise handles these in production
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Media files - Always serve (QR codes, uploads, etc.)
# This works in both DEBUG=True and DEBUG=False
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
