from django import forms
from .models import CertificateRequest


class CertificateRequestForm(forms.ModelForm):
    """
    Base form for certificate requests.
    Common fields are handled here; certificate-specific extras
    are collected via the frontend JS and stored in form_data.
    """

    class Meta:
        model = CertificateRequest
        fields = [
            "certificate_type",
            "first_name",
            "last_name",
            "middle_name",
            "sitio",
            "purpose",
            "appointment_time",
        ]
        widgets = {
            "certificate_type": forms.HiddenInput(),
            "first_name": forms.TextInput(attrs={
                "placeholder": "Juan",
                "class": "form-input w-full",
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Dela Cruz",
                "class": "form-input w-full",
            }),
            "middle_name": forms.TextInput(attrs={
                "placeholder": "Reyes",
                "class": "form-input w-full",
            }),
            "sitio": forms.TextInput(attrs={
                "placeholder": "e.g. Sitio Central",
                "class": "form-input w-full",
            }),
            "purpose": forms.HiddenInput(),
            "appointment_time": forms.HiddenInput(),
        }
