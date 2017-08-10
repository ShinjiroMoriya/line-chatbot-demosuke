from django import forms
from django.core.validators import MinLengthValidator

ERROR_MESSAGES = {
    'required': 'required',
    'min_length': 'min_length',
    'max_length': 'max_length',
}


class RegisterForm(forms.Form):
    line_id = forms.CharField(required=True,
                              max_length=255,
                              error_messages=ERROR_MESSAGES)
    email = forms.EmailField(required=True,
                             max_length=255,
                             validators=[MinLengthValidator(3)],
                             error_messages=ERROR_MESSAGES)
