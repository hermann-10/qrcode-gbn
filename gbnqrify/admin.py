from django.contrib import admin
from django.utils.html import format_html
from .models import Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'first_name', 'last_name', 'department', 'created_at', 'qr_code_preview']

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" width="50" height="50" style="object-fit: contain;" />'
                '</a>',
                obj.qr_code.url,
            )
        return "No QR Code"

    qr_code_preview.short_description = 'QR Code'
