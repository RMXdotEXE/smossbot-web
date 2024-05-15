from django_jsonform.models.fields import ArrayField
from django.db import models
from django.utils import timezone


class PatchNote(models.Model):
    title = models.CharField(max_length=50)
    date = models.DateField(blank=True)
    last_modified = models.DateTimeField()
    version = models.CharField(max_length=20, unique=True)
    notes = ArrayField(base_field=models.TextField())
    joke_note = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()
        self.last_modified = timezone.now()
        return super(PatchNote, self).save(*args, **kwargs)