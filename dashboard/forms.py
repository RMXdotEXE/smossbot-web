from django import forms
from django.core.exceptions import ValidationError


def file_size_checker(value):
    if value.size > 2 * 1024 * 1024:
        raise ValidationError('File size should be max 2MB.')
    return


class UploadForm(forms.Form):
    file = forms.FileField(label="File", required=True, validators=[file_size_checker])
    filename = forms.CharField(label="File name", required=True, max_length=100)