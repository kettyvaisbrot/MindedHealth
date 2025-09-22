from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('therapist', 'Therapist'),
        ('family', 'Family Member'),
    )

    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True)
    patient_email = forms.EmailField(
        required=False,
        help_text="Required if registering as a family member."
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        patient_email = cleaned_data.get("patient_email")

        if role == "family" and not patient_email:
            self.add_error("patient_email", "Patient email is required for family members.")

        return cleaned_data


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={"autofocus": True})
    )

    class Meta:
        model = User
        fields = ("username", "password")
