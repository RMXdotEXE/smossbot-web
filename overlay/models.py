from accounts.models import TwitchUser
from django.db import models


class SongReqOverlay(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    enabled = models.BooleanField(default=False)
    constant = models.BooleanField(default=False)
    background = models.BooleanField(default=False)
    vertical_anchor_pos = models.CharField(max_length=12, default="top")
    horizontal_anchor_pos = models.CharField(max_length=12, default="left")


class YTReqOverlay(models.Model):
    user = models.OneToOneField(TwitchUser, on_delete=models.CASCADE, primary_key=True)
    width = models.IntegerField(default=854)
    height = models.IntegerField(default=480)
    vertical_anchor_pos = models.CharField(max_length=12, default="top")
    horizontal_anchor_pos = models.CharField(max_length=12, default="right")