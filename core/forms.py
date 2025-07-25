# core/forms.py
from django import forms
from .models import Support, Client, CreditBalance
from django.core.exceptions import ValidationError

class SupportForm(forms.ModelForm):
    class Meta:
        model = Support
        # Definimos los campos que aparecerán en el formulario
        fields = [
            'client', 
            'support_channel', 
            'problem_description', 
            'solution_description', 
            'call_status',
            'kerberus_id', 
            'freshdesk_ticket', 
            'waiting_time', 
            'duration'
        ]

        # Asignamos clases de Bootstrap y placeholders para que se vea bien
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'support_channel': forms.Select(attrs={'class': 'form-select'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'solution_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'call_status': forms.Select(attrs={'class': 'form-select'}),
            'kerberus_id': forms.TextInput(attrs={'class': 'form-control'}),
            'freshdesk_ticket': forms.TextInput(attrs={'class': 'form-control'}),
            'waiting_time': forms.TextInput(attrs={'class': 'form-control duration-picker', 'placeholder': 'HH:MM:SS'}),
            'duration': forms.TextInput(attrs={'class': 'form-control duration-picker', 'placeholder': 'HH:MM:SS'}),
        }

        def clean(self):
            # Llama a la validación original primero
            cleaned_data = super().clean()
            
            call_status = cleaned_data.get("call_status")
            duration = cleaned_data.get("duration")

            # Verificamos solo si el estado es "RETURNED"
            if call_status and call_status.name == 'RETURNED':
                balance = CreditBalance.objects.first()
                
                # Calculamos la duración de esta llamada en minutos
                duration_in_minutes = duration.total_seconds() / 60 if duration else 0
                
                # Si no hay suficiente crédito, lanzamos un error
                if not balance or balance.remaining_minutes < duration_in_minutes:
                    raise ValidationError(
                        "There are not enough credits available to register this support."
                    )
            
            return cleaned_data # Siempre devuelve los datos limpios

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        # Campos que pediremos en el modal
        fields = ['name', 'client_type', 'country', 'email', 'phone']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_type': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    def clean_email(self):
        """ Valida que el email no exista ya. """
        email = self.cleaned_data.get('email')
        if Client.objects.filter(email__iexact=email).exists():
            raise ValidationError("A customer with this email already exists.")
        return email

    def clean_phone(self):
        """ Valida que el teléfono no exista ya (si se proporcionó). """
        phone = self.cleaned_data.get('phone')
        if phone and Client.objects.filter(phone__iexact=phone).exists():
            raise ValidationError("A customer with this number already exists.")
        return phone