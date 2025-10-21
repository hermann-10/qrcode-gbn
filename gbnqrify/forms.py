from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'created_at', 'department']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': 'Enter First Name',
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'Enter Last Name',
                'class': 'form-control'
            }),
            'created_at': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'department': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'created_at': 'Date of Joining',
            'department': 'Department',
        }
