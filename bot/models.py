from accounts.models import TwitchUser
from django.contrib.postgres.fields import ArrayField
from django.db import models


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