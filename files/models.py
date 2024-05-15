import os

from accounts.models import TwitchUser
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.dispatch import receiver


# CharFields we'll only use whenever we know the length of something, or if something is unlikely to be 50+ chars.
# TextField we'll use for codes, tokens, etc.; things that could be like a million light years long.


# VALIDATORS ==================================================
alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed')

def file_size_checker(value):
    if value.size > 2 * 1024 * 1024:
        raise ValidationError('File size should be max 2MB')
    return

def user_media_path(instance, filename):
    # {{ MEDIA_URL }}/username/filename
    return "{}/{}".format(instance.user.username, filename)


# FILES ===================================================
# Any files that are uploaded by users.
class UploadedFile(models.Model):
    # Use default Django id field, created automatically
    file = models.FileField(validators=[file_size_checker, FileExtensionValidator(allowed_extensions=["mp3", "wav", "ogg"])], upload_to=user_media_path)
    user = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)
    tag = models.CharField(max_length=32, blank=True, null=True, validators=[alphanumeric])
    upload_date = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    purposes = ArrayField(base_field=models.CharField(max_length=10), blank=True, null=True)

@receiver(models.signals.post_delete, sender=UploadedFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)