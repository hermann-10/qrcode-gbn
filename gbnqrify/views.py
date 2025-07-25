from datetime import time
from io import BytesIO
import uuid
import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.base import ContentFile

from django.views.decorators.csrf import csrf_exempt
from .forms import EmployeeForm
from .models import Employee, Attendance
import pytz
from django.shortcuts import render
from django.utils import timezone
from django.db.models.functions import TruncDay,TruncWeek, TruncMonth

from django.utils.timezone import now
from datetime import datetime, date, time, timedelta

from collections import defaultdict
from django.db.models import Q
from datetime import time as dt_time

import xlsxwriter



#Machine Learning
from sklearn.cluster import KMeans
import numpy as np



swiss_tz = pytz.timezone('Europe/Zurich')

# --- Utility ---
def is_admin(user):
    return user.is_superuser or user.is_staff

def get_current_session():
    now = timezone.now().time()
    return 'AM' if now <= time(13, 30) else 'PM'


# --- QR Scan Page ---
@csrf_exempt
def scan_qr(request):
    if request.method == 'POST':
        qr_data = request.POST.get('qr_data', '').strip()
        qr_data = qr_data.replace("'", "-")  # Fix UUID format

        try:
            uuid_obj = uuid.UUID(qr_data)
        except ValueError:
            return render(request, 'gbnqrify/scan_qr.html', {
                'feedback': '❌ Card invalid! Please visit reception for help'
            })

        try:
            employee = Employee.objects.get(uuid=uuid_obj)
        except Employee.DoesNotExist:
            return render(request, 'gbnqrify/scan_qr.html', {
                'feedback': '❌ Card invalid! Please visit reception for help'
            })

        now_dt = timezone.now().astimezone(swiss_tz)
        now_time = now_dt.time()
        now_date = now_dt.date()

        if now_time < time(12, 0):
            session = 'AM'
            scheduled = employee.am_start_time
        elif now_time >= time(13, 00):
            session = 'PM'
            scheduled = employee.pm_start_time
        else:
            return render(request, 'gbnqrify/scan_qr.html', {
                'feedback': '⏰ Scans between 12:00 PM and 01:00 PM are not considered. Please scan after 01:00 PM.'
            })

        attendance_exists = Attendance.objects.filter(
            employee=employee,
            date=now_date,
            session=session
        ).exists()

        if attendance_exists:
            return render(request, 'gbnqrify/scan_qr.html', {
                'feedback': f'ℹ️ Attendance for {session} session already recorded today. Thank you!'
            })

        status = 'On Time' if now_time <= scheduled else 'Delay'

        Attendance.objects.create(
            employee=employee,
            date=now_date,
            time=now_time,
            session=session,
            status=status
        )

        time_str = now_dt.strftime('%I:%M %p')
        message = (f"Hi! {employee.first_name} {employee.last_name}. Good job! Arrived on time! {time_str}"
                   if status == 'On Time' else
                   f"Hi! {employee.first_name} {employee.last_name}. You are delayed, try to come early! {time_str}")

        return render(request, 'gbnqrify/scan_qr.html', {'feedback': message})

    return render(request, 'gbnqrify/scan_qr.html')


# --- AJAX for Scanner ---
from datetime import time
from django.http import JsonResponse
from django.utils import timezone

def check_qr_ajax(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

    qr_data = request.POST.get('qr_data', '').strip()
    if not qr_data:
        return JsonResponse({'status': 'invalid', 'message': 'Card is invalid. Please contact the reception.'})

    try:
        employee = Employee.objects.get(uuid=qr_data)
    except Employee.DoesNotExist:
        return JsonResponse({'status': 'invalid', 'message': 'Card is invalid. Please contact the reception.'})

    now = timezone.now().astimezone(swiss_tz)
    now_time = now.time()
    now_date = now.date()

    # Define session time ranges
    am_on_time_start = time(8, 30)
    am_on_time_end = time(9, 0)
    am_delay_end = time(12, 0)

    pm_on_time_start = time(13, 0)
    pm_on_time_end = time(13, 30)
    pm_delay_end = time(17, 0)

    if am_on_time_start <= now_time <= am_delay_end:
        session = 'AM'
        if am_on_time_start <= now_time <= am_on_time_end:
            status = 'On Time'
        elif time(9, 1) <= now_time <= am_delay_end:
            status = 'Delay'
        else:
            return JsonResponse({'status': 'ignored', 'message': 'Scans before 08:30 AM are not allowed.'})

    elif pm_on_time_start <= now_time <= pm_delay_end:
        session = 'PM'
        if pm_on_time_start <= now_time <= pm_on_time_end:
            status = 'On Time'
        elif time(13, 31) <= now_time <= pm_delay_end:
            status = 'Delay'
        else:
            return JsonResponse({'status': 'ignored', 'message': 'Scans before 01:00 PM are not allowed.'})

    else:
        return JsonResponse({'status': 'ignored', 'message': 'Scans between 12:01 PM and 12:59 PM or outside working hours are not allowed.'})

    # Prevent duplicate attendance
    attendance_exists = Attendance.objects.filter(
        employee=employee,
        date=now_date,
        session=session
    ).exists()

    if attendance_exists:
        return JsonResponse({'status': 'exists', 'message': f'Attendance for {session} session already recorded today.'})

    Attendance.objects.create(
        employee=employee,
        date=now_date,
        time=now_time,
        session=session,
        status=status
    )

    time_str = now.strftime('%I:%M %p')
    msg = (
        f"Hi! {employee.first_name} {employee.last_name}. Good job! Arrived on time! {time_str}"
        if status == 'On Time'
        else f"Hi! {employee.first_name} {employee.last_name}. You are delayed, try to come early! {time_str}"
    )

    return JsonResponse({'status': 'ok', 'message': msg})



# --- Admin Dashboard ---
@login_required
@user_passes_test(is_admin)
def dashboard(request):
    selected_department = request.GET.get('department', '')
    departments = Employee.objects.values_list('department', flat=True).distinct().order_by('department')
    employees = Employee.objects.filter(department=selected_department) if selected_department else Employee.objects.all()
    return render(request, 'gbnqrify/dashboard.html', {
        'departments': departments,
        'employees': employees,
        'selected_department': selected_department
    })


# --- Employee Register ---
@login_required
@user_passes_test(is_admin)
def employee_register(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            qr = qrcode.make(str(employee.uuid))
            buffer = BytesIO()
            qr.save(buffer)
            employee.qr_code.save(f"{employee.uuid}.png", ContentFile(buffer.getvalue()), save=True)
            return JsonResponse({"success": True})
        else:
            # Send back errors as string (you can customize this)
            errors = form.errors.as_json()
            return JsonResponse({"success": False, "error": errors})
    else:
        form = EmployeeForm()
        return render(request, 'gbnqrify/employee_register.html', {'form': form})


def register_employee(request):
    return render(request, 'gbnqrify/employee_register.html')

# --- Employee Filter View ---
@login_required
@user_passes_test(is_admin)
def employee_filter(request):
    departments = Employee.objects.values_list('department', flat=True).distinct().order_by('department')
    selected_department = request.GET.get('department', '')
    employees = Employee.objects.filter(department=selected_department) if selected_department else Employee.objects.all()
    return render(request, 'gbnqrify/employee_filter.html', {
        'departments': departments,
        'employees': employees,
        'selected_department': selected_department
    })


# --- Employee Detail View (for QR print) ---
@login_required
@user_passes_test(is_admin)
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    return render(request, 'gbnqrify/employee_detail.html', {'employee': employee})


# --- QR Code Print View ---
@login_required
@user_passes_test(is_admin)
def employee_qr_print(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    return render(request, 'gbnqrify/employee_qr_print.html', {'employee': employee})


# --- Employee Data View ---
@login_required
@user_passes_test(is_admin)
def employee_data(request):
    employees = Employee.objects.all()
    return render(request, 'gbnqrify/employee_data.html', {'employees': employees})


# --- Employee List View ---
@login_required
@user_passes_test(is_admin)
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'gbnqrify/employee_list.html', {'employees': employees})


# --- Edit Employee ---
@login_required
@user_passes_test(is_admin)
def edit_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Employee updated successfully.")
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'gbnqrify/edit_employee.html', {'form': form})


# --- Delete Employee ---
@login_required
@user_passes_test(is_admin)
def delete_employee(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully.')
    return redirect('employee_filter')  # Stay on the same page


def get_attendance_data(request):
    today = timezone.now().date()

    # --- 1. Daily: Past 7 days ---
    daily_labels = [(today - timedelta(days=i)).strftime('%a') for i in reversed(range(7))]
    daily_counts = [0] * 7
    daily_query = (
        Attendance.objects
        .filter(date__range=(today - timedelta(days=6), today))
        .annotate(day=TruncDay('date'))
        .values('day')
        .annotate(count=Count('id'))
    )
    for entry in daily_query:
        day_label = entry['day'].strftime('%a')
        if day_label in daily_labels:
            idx = daily_labels.index(day_label)
            daily_counts[idx] = entry['count']

    # --- 2. Weekly: Last 3 full weeks ---
    current_week_start = today - timedelta(days=today.weekday())
    weeks = [current_week_start - timedelta(weeks=i+1) for i in reversed(range(3))]
    weekly_labels = [f"Week {w.isocalendar()[1]}" for w in weeks]
    weekly_counts = [0] * 3
    weekly_query = (
        Attendance.objects
        .filter(date__gte=weeks[0])
        .annotate(week=TruncWeek('date'))
        .values('week')
        .annotate(count=Count('id'))
    )
    for entry in weekly_query:
        week_num = entry['week'].isocalendar()[1]
        label = f"Week {week_num}"
        if label in weekly_labels:
            idx = weekly_labels.index(label)
            weekly_counts[idx] = entry['count']

    # --- 3. Monthly: Last 3 full months ---
    current_month = today.replace(day=1)
    months = [(current_month - timedelta(days=30*i)).replace(day=1) for i in reversed(range(3))]
    month_labels = [m.strftime("%b") for m in months]
    month_counts = [0] * 3
    monthly_query = (
        Attendance.objects
        .filter(date__gte=months[0])
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
    )
    for entry in monthly_query:
        month_label = entry['month'].strftime("%b")
        if month_label in month_labels:
            idx = month_labels.index(month_label)
            month_counts[idx] = entry['count']

    # --- 4. Presence vs Absence (Last 30 days) ---
    presence_counts = {'present': 0, 'absent': 0}
    presence_query = (
        Attendance.objects
        .filter(date__gte=today - timedelta(days=30))
        .values('status')
        .annotate(count=Count('id'))
    )
    for entry in presence_query:
        status = entry['status'].lower()
        if status == 'present':
            presence_counts['present'] = entry['count']
        elif status == 'absent':
            presence_counts['absent'] = entry['count']

    return JsonResponse({
        'daily': {
            'labels': daily_labels,
            'counts': daily_counts
        },
        'weekly': {
            'labels': weekly_labels,
            'counts': weekly_counts
        },
        'monthly': {
            'labels': month_labels,
            'counts': month_counts
        },
        'presence': {
            'labels': ['Present', 'Absent'],
            'counts': [presence_counts['present'], presence_counts['absent']]
        }
    })
    
    
def department_attendance_data(request):
    from datetime import datetime, timedelta

    now = datetime.now()

    # Daily: Today
    daily = Attendance.objects.filter(date=now.date()).values('employee__department').annotate(count=Count('id'))

    # Weekly: Past 7 days
    last_week = now - timedelta(days=7)
    weekly = Attendance.objects.filter(date__gte=last_week).values('employee__department').annotate(count=Count('id'))

    # Monthly: Past 30 days
    last_month = now - timedelta(days=30)
    monthly = Attendance.objects.filter(date__gte=last_month).values('employee__department').annotate(count=Count('id'))

    # Most vs Least
    total = Attendance.objects.values('employee__department').annotate(count=Count('id')).order_by('-count')
    most = total.first()
    least = total.last()

    return JsonResponse({
        'daily': {
            'labels': [entry['employee__department'] for entry in daily],
            'counts': [entry['count'] for entry in daily]
        },
        'weekly': {
            'labels': [entry['employee__department'] for entry in weekly],
            'counts': [entry['count'] for entry in weekly]
        },
        'monthly': {
            'labels': [entry['employee__department'] for entry in monthly],
            'counts': [entry['count'] for entry in monthly]
        },
        'most_least': {
            'labels': [most['employee__department'] if most else 'N/A', least['employee__department'] if least else 'N/A'],
            'counts': [most['count'] if most else 0, least['count'] if least else 0]
        }
    })
    
def employee_analytics(request):
    employees = Employee.objects.all()
    start_date = now().date() - timedelta(days=7)  # last 7 days
    end_date = now().date()

    # Fetch attendance entries only for QR scanned sessions (exclude manual)
    attendance_qs = Attendance.objects.filter(date__range=(start_date, end_date))

    attendance_map = defaultdict(lambda: {'AM': 'WH', 'PM': 'WH'})

    for att in attendance_qs:
        session = att.session
        if att.employee and session in ['AM', 'PM']:
            attendance_map[(att.employee.uuid, att.date)][session] = 'IP'

    # Create daily attendance status per employee
    daily_data = []
    for employee in employees:
        emp_row = {'employee': employee, 'records': []}
        for day_offset in range(7):
            day = end_date - timedelta(days=day_offset)
            sessions = attendance_map.get((employee.uuid, day), {'AM': 'WH', 'PM': 'WH'})
            emp_row['records'].append({
                'date': day.strftime('%d-%m'),
                'AM': sessions['AM'],
                'PM': sessions['PM']
            })
        daily_data.append(emp_row)

    context = {
        'employees': employees,
        'daily_data': daily_data
    }
    return render(request, 'gbnqrify/employee_analytics.html', context)

    
def fetch_employee_data(request):
    uuid_str = request.GET.get('uuid')
    if not uuid_str:
        return JsonResponse({'error': 'UUID not provided'}, status=400)

    try:
        uuid_obj = uuid.UUID(uuid_str)
    except ValueError:
        return JsonResponse({'error': 'Invalid UUID format'}, status=400)

    # Filter only QR-scanned data (adjust 'scanned' logic as per your model)
    scanned_data = Attendance.objects.filter(employee__uuid=uuid_obj).order_by('date')

    # Daily data
    daily_data = scanned_data.values('date').annotate(count=Count('id')).order_by('date')

    # Weekly data
    week_data = {}
    for entry in scanned_data:
        week_start = entry.date - timedelta(days=entry.date.weekday())
        week_data[week_start] = week_data.get(week_start, 0) + 1

    # Monthly data
    month_data = {}
    for entry in scanned_data:
        key = entry.date.strftime("%Y-%m")
        month_data[key] = month_data.get(key, 0) + 1

    # Daily status (all employees)
    all_employees = Employee.objects.all()
    today = date.today()
    status_list = []
    for emp in all_employees:
        scanned = Attendance.objects.filter(employee=emp, date=today).exists()
        status_list.append({
            'name': f"{emp.first_name} {emp.last_name}",
            'uuid': str(emp.uuid),
            'status': 'IP' if scanned else 'WH',
        })

    return JsonResponse({
        'daily_data': list(daily_data),
        'weekly_data': [{'week': str(k), 'count': v} for k, v in week_data.items()],
        'monthly_data': [{'month': k, 'count': v} for k, v in month_data.items()],
        'status_list': status_list
    })
    
    
def fetch_attendance_status_today(request):
    try:
        today = now().date()
        employees = Employee.objects.all()
        status_list = []

        for emp in employees:
            am_present = Attendance.objects.filter(
                employee=emp,
                date=today,
                time__lt=dt_time(12, 0)
            ).exists()

            pm_present = Attendance.objects.filter(
                employee=emp,
                date=today,
                time__gte=dt_time(12, 0)
            ).exists()

            status_list.append({
                'name': f'{emp.first_name} {emp.last_name}',
                'AM': 'IP' if am_present else 'WH',
                'PM': 'IP' if pm_present else 'WH',
            })

        return JsonResponse({'status_list': status_list})
    except Exception as e:
        # return error for debugging
        return JsonResponse({'error': str(e)}, status=500)
    
    
    
@login_required
@user_passes_test(is_admin) 
def download_employee_excel(request):
    uuid = request.GET.get('uuid')
    employee = Employee.objects.filter(uuid=uuid).first()
    if not employee:
        return HttpResponse('Employee not found.', status=404)

    today = now().date()

    # Get AM attendance
    am_attendance = Attendance.objects.filter(
        employee=employee,
        date=today,
        session='AM'
    ).order_by('time').first()

    # Get PM attendance
    pm_attendance = Attendance.objects.filter(
        employee=employee,
        date=today,
        session='PM'
    ).order_by('time').first()

    # Define time thresholds
    AM_CUTOFF = dt_time(9, 0)
    PM_CUTOFF = dt_time(13, 30)

    # Determine AM status and scan time
    if am_attendance:
        am_scan_time = am_attendance.time.strftime('%H:%M')
        am_status = 'On Time' if am_attendance.time < AM_CUTOFF else 'Delay'
    else:
        am_scan_time = '-'
        am_status = 'WH'

    # Determine PM status and scan time
    if pm_attendance:
        pm_scan_time = pm_attendance.time.strftime('%H:%M')
        pm_status = 'On Time' if pm_attendance.time <= PM_CUTOFF else 'Delay'
    else:
        pm_scan_time = '-'
        pm_status = 'WH'

    # Create Excel
    today_str = today.strftime('%d.%m.%Y')
    buf = BytesIO()
    wb = xlsxwriter.Workbook(buf, {'in_memory': True})
    ws = wb.add_worksheet('Presence')

    # Formatting
    tf = wb.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
    df = wb.add_format({'italic': True, 'font_size': 10, 'align': 'center'})
    hf = wb.add_format({'bold': True, 'border': 1, 'align': 'center'})
    cf = wb.add_format({'border': 1, 'align': 'center'})

    # Headers and layout
    ws.merge_range('A1:E1', 'GBN Employee Presence', tf)
    ws.merge_range('A2:E2', f'Date: {today_str}', df)
    ws.write('A4', 'Name', hf)
    ws.write('B4', 'AM Scan', hf)
    ws.write('C4', 'AM Status', hf)
    ws.write('D4', 'PM Scan', hf)
    ws.write('E4', 'PM Status', hf)

    # Row with data
    ws.write('A5', f"{employee.first_name} {employee.last_name}", cf)
    ws.write('B5', am_scan_time, cf)
    ws.write('C5', am_status, cf)
    ws.write('D5', pm_scan_time, cf)
    ws.write('E5', pm_status, cf)

    # Column width
    ws.set_column('A:A', 25)
    ws.set_column('B:E', 15)

    # Finalize and return
    wb.close()
    buf.seek(0)
    return HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=employee_presence.xlsx'}
    )
    
@user_passes_test(is_admin)
def export_attendance_excel(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    dept_id = request.GET.get('department_id')

    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()

    employees = Employee.objects.all()
    if dept_id:
        employees = employees.filter(department_id=dept_id)

    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    buf = BytesIO()
    wb = xlsxwriter.Workbook(buf, {'in_memory': True})
    ws = wb.add_worksheet('Weekly Attendance')

    # Header
    headers = ["Date", "Department", "Employee", "AM Scan", "AM Status", "PM Scan", "PM Status"]
    for col, header in enumerate(headers):
        ws.write(0, col, header)

    AM_CUTOFF = datetime.strptime("09:00", "%H:%M").time()
    PM_CUTOFF = datetime.strptime("13:30", "%H:%M").time()

    row = 1
    for date in date_range:
        for emp in employees:
            dept_name = emp.get_department_display() if emp.department else "N/A"


            am_att = Attendance.objects.filter(employee=emp, date=date, session='AM').order_by('time').first()
            pm_att = Attendance.objects.filter(employee=emp, date=date, session='PM').order_by('time').first()

            if am_att:
                am_time = am_att.time.strftime("%H:%M")
                am_status = "On Time" if am_att.time < AM_CUTOFF else "Delay"
            else:
                am_time = "-"
                am_status = "WH"

            if pm_att:
                pm_time = pm_att.time.strftime("%H:%M")
                pm_status = "On Time" if pm_att.time <= PM_CUTOFF else "Delay"
            else:
                pm_time = "-"
                pm_status = "WH"

            ws.write(row, 0, date.strftime("%Y-%m-%d"))
            ws.write(row, 1, dept_name)
            ws.write(row, 2, f"{emp.first_name} {emp.last_name}")
            ws.write(row, 3, am_time)
            ws.write(row, 4, am_status)
            ws.write(row, 5, pm_time)
            ws.write(row, 6, pm_status)
            row += 1

    wb.close()
    buf.seek(0)
    return HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="weekly_attendance_summary.xlsx"'}
    ) 
    

    
def general_view(request):
    return render(request, 'gbnqrify/general.html')   
    
    
def department_analytics(request):
    return render(request, 'gbnqrify/department_analytics.html')



def analytics_dashboard(request):
    return render(request, 'gbnqrify/dashboard.html')

def attendance_clustering_view(request):
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    employees = Employee.objects.all()

    attendance_map = defaultdict(lambda: defaultdict(lambda: {'AM': None, 'PM': None}))
    attendances = Attendance.objects.filter(date__range=(start_date, end_date))

    # Organize attendance records per employee per day per session
    for att in attendances:
        day = att.date
        if att.is_morning():
            attendance_map[att.employee.uuid][day]['AM'] = att
        elif att.is_afternoon():
            attendance_map[att.employee.uuid][day]['PM'] = att

    stats = {}
    for emp in employees:
        emp_days = attendance_map[emp.uuid]
        total_days = (end_date - start_date).days + 1

        am_present = 0
        pm_present = 0
        full_day = 0
        am_delay = 0
        pm_delay = 0

        am_times = []
        pm_times = []

        for single_day in (start_date + timedelta(n) for n in range(total_days)):
            am_att = emp_days.get(single_day, {}).get('AM')
            pm_att = emp_days.get(single_day, {}).get('PM')

            am_flag = am_att is not None
            pm_flag = pm_att is not None

            if am_flag:
                am_present += 1
                if am_att.is_delayed():
                    am_delay += 1
                if am_att.time:
                    am_times.append(datetime.combine(single_day, am_att.time))
            if pm_flag:
                pm_present += 1
                if pm_att.is_delayed():
                    pm_delay += 1
                if pm_att.time:
                    pm_times.append(datetime.combine(single_day, pm_att.time))
            if am_flag and pm_flag:
                full_day += 1

        # Calculate presence ratios
        am_ratio = am_present / total_days
        pm_ratio = pm_present / total_days
        full_day_ratio = full_day / total_days
        am_delay_ratio = am_delay / am_present if am_present else 0
        pm_delay_ratio = pm_delay / pm_present if pm_present else 0

        # Calculate average scan times for AM and PM sessions (if any)
        avg_am_time = None
        avg_pm_time = None

        if am_times:
            avg_am_time = (sum([dt.time().hour * 3600 + dt.time().minute * 60 + dt.time().second for dt in am_times]) // len(am_times))
            avg_am_time = time(hour=avg_am_time // 3600, minute=(avg_am_time % 3600) // 60, second=avg_am_time % 60)

        if pm_times:
            avg_pm_time = (sum([dt.time().hour * 3600 + dt.time().minute * 60 + dt.time().second for dt in pm_times]) // len(pm_times))
            avg_pm_time = time(hour=avg_pm_time // 3600, minute=(avg_pm_time % 3600) // 60, second=avg_pm_time % 60)

        expected_am_time = time(9, 15)
        expected_pm_time = time(13, 30)

        am_status = 'No Data'
        pm_status = 'No Data'

        if avg_am_time:
            am_status = 'On Time' if avg_am_time <= expected_am_time else 'Late'
        if avg_pm_time:
            pm_status = 'On Time' if avg_pm_time <= expected_pm_time else 'Late'

        
        
        stats[emp.uuid] = {
            'employee': emp,
            'am_ratio': am_ratio,
            'pm_ratio': pm_ratio,
            'full_day_ratio': full_day_ratio,
            'am_delay_ratio': am_delay_ratio,
            'pm_delay_ratio': pm_delay_ratio,
            'avg_am_time': avg_am_time,
            'avg_pm_time': avg_pm_time,
            'am_status': am_status,
            'pm_status': pm_status,
                    
            }

    # Clustering 
    X = np.array([
        [v['am_ratio'], v['pm_ratio'], v['full_day_ratio']] for v in stats.values()
    ])

    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(X)

    cluster_centers = kmeans.cluster_centers_
    cluster_labels = {}
    for idx, center in enumerate(cluster_centers):
        max_idx = np.argmax(center)
        if max_idx == 0:
            cluster_labels[idx] = "Mostly AM Office"
        elif max_idx == 1:
            cluster_labels[idx] = "Mostly PM Office"
        else:
            cluster_labels[idx] = "Mostly Full Day Office"

    for i, emp_id in enumerate(stats.keys()):
        stats[emp_id]['cluster'] = int(clusters[i])

    context = {
        'stats': stats.values(),
        'cluster_labels': cluster_labels,
    }

    return render(request, 'gbnqrify/attendance_clustering.html', context)

def employee_uuid_api(request):
    password = request.headers.get('X-API-Password')  # Case-sensitive
    print("Received password:", password)
    if password != 'anothjeev_qrify_uuid':
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    employees = Employee.objects.all().values('id', 'full_name', 'uuid')
    return JsonResponse(list(employees), safe=False)
