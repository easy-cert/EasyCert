from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.ModelForm):
    """
    Registration form for residents.
    Collects: name, address, age, birthdate, contact, email, password.
    """

    first_name = forms.CharField(
        max_length=75,
        widget=forms.TextInput(attrs={
            "placeholder": "Juan",
            "class": "form-input w-full",
        }),
    )
    last_name = forms.CharField(
        max_length=75,
        widget=forms.TextInput(attrs={
            "placeholder": "Dela Cruz",
            "class": "form-input w-full",
        }),
    )
    middle_name = forms.CharField(
        max_length=75,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Reyes",
            "class": "form-input w-full",
        }),
    )
    address = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            "placeholder": "123 Sampaguita St., Sitio Central, Cebu City",
            "class": "form-input w-full",
        }),
    )
    age = forms.IntegerField(
        min_value=1,
        max_value=150,
        widget=forms.NumberInput(attrs={
            "placeholder": "25",
            "class": "form-input w-full",
        }),
    )
    birthdate = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-input w-full",
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Min. 6 characters",
            "class": "form-input w-full",
        }),
        min_length=6,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Re-enter your password",
            "class": "form-input w-full",
        }),
    )

    class Meta:
        model = User
        fields = ["email", "contact_number"]
        widgets = {
            "email": forms.EmailInput(attrs={
                "placeholder": "juan@example.com",
                "class": "form-input w-full",
            }),
            "contact_number": forms.TextInput(attrs={
                "placeholder": "09XX XXX XXXX",
                "class": "form-input w-full",
            }),
        }

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        cpw = cleaned.get("confirm_password")
        if pw and cpw and pw != cpw:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        fn = self.cleaned_data["first_name"]
        ln = self.cleaned_data["last_name"]
        mn = self.cleaned_data.get("middle_name", "")
        user.full_name = f"{fn} {mn} {ln}".replace("  ", " ").strip()
        user.address = self.cleaned_data["address"]
        user.age = self.cleaned_data["age"]
        user.birthdate = self.cleaned_data["birthdate"]
        user.set_password(self.cleaned_data["password"])
        user.role = User.USER
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Simple email + password login form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "placeholder": "you@example.com",
            "class": "form-input w-full",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Password / 6-digit PIN",
            "class": "form-input w-full",
        }),
    )


class AdminRegistrationForm(forms.ModelForm):
    """Form for Super Admin to register Barangay Admins."""
    pin = forms.CharField(
        min_length=6,
        max_length=6,
        widget=forms.PasswordInput(attrs={
            "placeholder": "6-digit PIN",
            "class": "form-input w-full",
        }),
    )

    class Meta:
        model = User
        fields = [
            "full_name", "birthdate", "age", "address", 
            "contact_number", "email", "barangay", "position"
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-input w-full"}),
            "birthdate": forms.DateInput(attrs={"type": "date", "class": "form-input w-full"}),
            "age": forms.NumberInput(attrs={"class": "form-input w-full"}),
            "address": forms.TextInput(attrs={"class": "form-input w-full"}),
            "contact_number": forms.TextInput(attrs={"class": "form-input w-full"}),
            "email": forms.EmailInput(attrs={"class": "form-input w-full"}),
            "barangay": forms.Select(attrs={"class": "form-input w-full"}),
            "position": forms.TextInput(attrs={"class": "form-input w-full", "placeholder": "e.g. Secretary, Captain"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["pin"])
        user.role = User.ADMIN
        user.is_staff = True # Needed for admin access if using django admin, but we are building custom
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for residents to update their profile information."""

    class Meta:
        model = User
        fields = ["full_name", "email", "contact_number", "address", "age", "birthdate"]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-input w-full",
                "placeholder": "Juan Dela Cruz",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input w-full",
                "placeholder": "juan@example.com",
            }),
            "contact_number": forms.TextInput(attrs={
                "class": "form-input w-full",
                "placeholder": "09XX XXX XXXX",
            }),
            "address": forms.TextInput(attrs={
                "class": "form-input w-full",
                "placeholder": "123 Sampaguita St., Cebu City",
            }),
            "age": forms.NumberInput(attrs={
                "class": "form-input w-full",
                "placeholder": "25",
            }),
            "birthdate": forms.DateInput(attrs={
                "type": "date",
                "class": "form-input w-full",
            }),
        }


class PasswordChangeForm(forms.Form):
    """Form for residents to change their password."""
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-input w-full",
            "placeholder": "Enter current password",
        }),
    )
    new_password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            "class": "form-input w-full",
            "placeholder": "Min. 6 characters",
        }),
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-input w-full",
            "placeholder": "Re-enter new password",
        }),
    )

    def clean(self):
        cleaned = super().clean()
        new_pw = cleaned.get("new_password")
        confirm_pw = cleaned.get("confirm_new_password")
        if new_pw and confirm_pw and new_pw != confirm_pw:
            self.add_error("confirm_new_password", "New passwords do not match.")
        return cleaned


from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(UserCreationForm):
    """Custom creation form for the Django admin."""
    class Meta:
        model = User
        fields = ("email", "full_name", "role", "barangay")

class CustomUserChangeForm(UserChangeForm):
    """Custom change form for the Django admin."""
    class Meta:
        model = User
        fields = ("email", "full_name", "role", "barangay")
