import uuid
from io import BytesIO
import qrcode
from django.db import models
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, time


class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('HR', 'Human Resources'),
        ('IT', 'Information Technology'),
        ('ADM', 'Administration'),
        ('COM', 'Communication'),
        ('MUL', 'Multimedia'),
        ('ACC', 'Accounts'),
        ('EDT', 'Editorial'),
        ('Stf', 'Staff'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES)
    date_birth = models.DateField(null=True, blank=True)
    created_at = models.DateField(default=timezone.now)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    # Expected start times for AM and PM sessions
    am_start_time = models.TimeField(default=time(9, 0))
    pm_start_time = models.TimeField(default=time(13, 30))

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.department})"

    def save(self, *args, **kwargs):
        force_regen = kwargs.pop('force_regen_qr', False)

        if not self.qr_code or force_regen:
            full_name = f"{self.first_name} {self.last_name}"
            qr_content = str(self.uuid)

            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(qr_content)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            filename = f"{full_name}_qr.png".replace(" ", "_")
            self.qr_code.save(filename, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)

    def clone(self):
        clone = Employee.objects.get(pk=self.pk)
        clone.pk = None
        clone.uuid = uuid.uuid4()  # new unique UUID for clone
        clone.qr_code = None       # clear QR so it regenerates on save
        clone.save()
        return clone


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    session = models.CharField(
        max_length=2,
        choices=[('AM', 'AM'), ('PM', 'PM')],
        null=True,
        blank=True
    )
    time = models.TimeField(auto_now_add=True, null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Present'
    )

    class Meta:
        unique_together = ('employee', 'date', 'session')
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.session} - {self.status}"

    def is_morning(self):
        """
        Returns True if this attendance record is for a morning session before 12:00 PM.
        """
        return self.session == 'AM' and self.time and self.time <= time(12, 0)

    def is_afternoon(self):
        """
        Returns True if this attendance record is for an afternoon session after 12:00 PM.
        """
        return self.session == 'PM' and self.time and self.time >= time(12, 0)

    def is_delayed(self):
        """
        Returns True if the attendance is considered delayed based on expected start time.
        """
        if not self.time:
            return False

        if self.session == 'AM' and self.employee.am_start_time:
            return self.time > self.employee.am_start_time
        elif self.session == 'PM' and self.employee.pm_start_time:
            return self.time > self.employee.pm_start_time

        return False
    
