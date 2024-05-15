from .models import PatchNote
from django.forms import ModelForm, TextInput, Textarea, DateInput


class ChangelogForm(ModelForm):
    class Meta:
        model = PatchNote
        fields = ['title', 'date', 'version', 'notes', 'joke_note']
        widgets = {
            'title': TextInput(attrs={
                'class': "",
                'placeholder': "",
            }),
            'date': DateInput(attrs={
                'class': "",
                'placeholder': "",
                'type': "date",
            }),
            'version': TextInput(attrs={
                'class': "",
                'placeholder': "",
            }),
            'notes': Textarea(attrs={
                'class': "",
                'placeholder': "",
            }),
            'joke_note': TextInput(attrs={
                'class': "",
                'placeholder': "",
            }),
        }