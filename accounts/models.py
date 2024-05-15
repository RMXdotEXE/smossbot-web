from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.db import models


# General information about a user
class TwitchUser(AbstractUser):
    twitch_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=25, unique=True)
    active_session = models.BooleanField(default=False)
    is_affiliate = models.BooleanField(default=False)

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