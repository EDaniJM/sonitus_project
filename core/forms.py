# core/forms.py
from django import forms
from .models import Support, Client, CreditBalance, Company
from django.core.exceptions import ValidationError


class ClientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Construimos el texto completo del cliente
        full_name = f"{obj.name} {obj.lastname or ''}".strip()
        company = f" - {obj.company.name}" if obj.company else ""
        return f"{full_name}{company}"


class SupportForm(forms.ModelForm):
    client = ClientChoiceField(
        queryset=Client.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    duration = forms.DurationField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control duration-picker',
            'placeholder': 'HH:MM:SS'
        })
    )
    waiting_time = forms.DurationField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control duration-picker',
            'placeholder': 'HH:MM:SS'
        })
    )

    class Meta:
        model = Support
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
        widgets = {
            'support_channel': forms.Select(attrs={'class': 'form-select'}),
            'problem_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'solution_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'call_status': forms.Select(attrs={'class': 'form-select'}),
            'kerberus_id': forms.TextInput(attrs={'class': 'form-control'}),
            'freshdesk_ticket': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def _parse_duration(self, value):
        try:
            h, m, s = map(int, value.split(":"))
            return timedelta(hours=h, minutes=m, seconds=s)
        except:
            return None

    def clean(self):
        cleaned_data = super().clean()

        support_channel = cleaned_data.get("support_channel")
        call_status = cleaned_data.get("call_status")
        duration = cleaned_data.get("duration")
        waiting_time = cleaned_data.get("waiting_time")
        freshdesk_ticket = cleaned_data.get("freshdesk_ticket")

        # Convertir strings en timedelta (si es necesario)
        for field in ['duration', 'waiting_time']:
            val = cleaned_data.get(field)
            if isinstance(val, str):
                parsed = self._parse_duration(val)
                if parsed is None:
                    self.add_error(field, "Invalid format, expected HH:MM:SS")
                else:
                    cleaned_data[field] = parsed

        if not support_channel:
            return cleaned_data

        is_call = getattr(support_channel, 'is_call', False)

        # Regla 1: Llamada recibida/devuelta => duration obligatorio
        if is_call and call_status and getattr(call_status, 'name', None) != 'MISSED':
            if not duration or duration.total_seconds() == 0:
                self.add_error(
                    'duration', "Duration is required for received or returned calls.")

        # Regla 2: Llamada perdida => waiting_time obligatorio
        if is_call and call_status and getattr(call_status, 'name', None) == 'MISSED':
            if not waiting_time or waiting_time.total_seconds() == 0:
                self.add_error(
                    'waiting_time', "Waiting time is required for missed calls.")

        # Regla 3: Canal FreshDesk => ticket obligatorio
        if 'FreshDesk' in getattr(support_channel, 'name', '') and not freshdesk_ticket:
            self.add_error('freshdesk_ticket',
                           "FreshDesk Ticket ID is required for this channel.")

        # Regla 4: Validación de crédito para llamadas devueltas
        if call_status and getattr(call_status, 'name', None) == 'RETURNED':
            balance = CreditBalance.objects.first()
            duration_in_minutes = duration.total_seconds() / 60 if duration else 0
            if not balance or balance.remaining_minutes < duration_in_minutes:
                raise ValidationError(
                    "There are not enough credits available to register this support.")

        return cleaned_data


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company name'}),
        }


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        # Campos que pediremos en el modal
        fields = ['name', 'lastname', 'company',
                  'client_type', 'country', 'email', 'phone']

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'lastname': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
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
            raise ValidationError(
                "A customer with this number already exists.")
        return phone
