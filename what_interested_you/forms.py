# forms.py

from django import forms


class InquiryForm(forms.Form):
    CHOICES = [
        ("symptoms", "Symptoms"),
        ("treatments", "Treatments"),
        ("coping", "Coping Strategies"),
    ]
    choice = forms.ChoiceField(
        choices=CHOICES, label="What do you want to know more about?"
    )
