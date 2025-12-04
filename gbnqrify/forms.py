from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'date_birth', 'created_at', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Enter First Name',
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Enter Last Name',
                'class': 'form-control'
            }),
            'date_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
            'created_at': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'date_birth': 'Date of Birth',
            'created_at': 'Date of Joining',
            'department': 'Department',
        }
