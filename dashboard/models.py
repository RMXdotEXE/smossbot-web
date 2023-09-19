import os

from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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


# IDENTIFICATIONS =============================================
# 

# General information about a user
class TwitchUser(models.Model):
    twitch_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=25)
    active_session = models.BooleanField(default=False)

# Information about a user's twitch credentials
class TwitchCredentials(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    code = models.TextField()
    access_token = models.TextField()
    expires_in = models.IntegerField()
    refresh_token = models.TextField()
    token_type = models.CharField(max_length=50)    # This will only ever be "Bearer" or "Code" or something like that
    scope = ArrayField(base_field=models.CharField(max_length=50))
    
# Information about a user's spotify credentials
class SpotifyCredentials(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    code = models.TextField()
    access_token = models.TextField()
    expires_in = models.IntegerField()
    refresh_token = models.TextField()
    token_type = models.CharField(max_length=50)
    scope = ArrayField(base_field=models.CharField(max_length=50))
    
# Information about channel point rewards
class ChannelPointReward(models.Model):
    reward_id = models.TextField(primary_key=True)
    user = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)
    reward_title = models.CharField(max_length=45)
    bot_created = models.BooleanField(default=False)    # If smossbot created it
    binded_to = ArrayField(base_field=models.CharField(max_length=20), default=list)


# FILES ===================================================
# Any files that are uploaded by users.
class UploadedFile(models.Model):
    # Use default Django id field, created automatically
    file = models.FileField(validators=[file_size_checker], upload_to=user_media_path)
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


# VARIABLES ==================================================
# Variables allow users to fine-tune specific behaviours about smossbot.

# Variables for song requests.
class SongReqVars(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    emote = models.CharField(max_length=100, default="Okayge")      # For those dumb long emote names

# Variables for song skips.
class SongSkipVars(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    emote = models.CharField(max_length=100, default="PepeLaugh")   # For those dumb long emote names

# Variables for ChatGPT image requests.
class GPTImageVars(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    imagesize = models.IntegerField(default=2)

# Variables for ChatGPT; some should be uneditable
class ChatGPTVars(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    clearsize = models.IntegerField(default=6)
    conversation = ArrayField(base_field=models.JSONField(), default=list)
    showfull = models.BooleanField(default=False)
    maxprompttokens = models.IntegerField(default=256)
    tokensused = models.IntegerField(default=0)

# Variables for YouTube requests.
class YTReqVars(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    maxsecs = models.IntegerField(default=60)
    mutespotify = models.BooleanField(default=True)