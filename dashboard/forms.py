#from .models import UploadedFile
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.forms import ModelForm, FileInput, TextInput


# VALIDATORS ==================================================
def file_size_checker(value):
    if value.size > 2 * 1024 * 1024:
        raise ValidationError('File size should be max 2MB.')
    return

"""
class UploadForm(ModelForm):
    # file = forms.FileField(validators=[file_size_checker])
    # tag = forms.CharField(validators=[alphanumeric])
    class Meta:
        model = UploadedFile
        fields = ['file', 'tag']
        widgets = {
            'file': FileInput(attrs={
                'class': "form-control compressCenter",
            }),
            'tag': TextInput(attrs={
                'class': "form-control compressCenter",
                'placeholder': "",
                'aria-describedby': "basic-addon3 basic-addon4",
            })
        }
"""