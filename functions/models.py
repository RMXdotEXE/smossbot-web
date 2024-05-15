import os

from accounts.models import TwitchUser
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models
from django.dispatch import receiver


# CharFields we'll only use whenever we know the length of something, or if something is unlikely to be 50+ chars.
# TextField we'll use for codes, tokens, etc.; things that could be like a million light years long.
    
# Information about channel point rewards
class ChannelPointReward(models.Model):
    reward_id = models.TextField(primary_key=True)
    user = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)
    reward_title = models.CharField(max_length=45)
    color = models.CharField(max_length=10) # Only ever a hex string; max will only ever be 7 prob
    image = models.CharField(max_length=256)    # No real way to determine max length of static url. Avg seems to be 150ish
    bot_created = models.BooleanField(default=False)    # If smossbot created it
    binded_to = ArrayField(base_field=models.CharField(max_length=20), default=list)

# Information about commands binded to functions.
class CommandFunction(models.Model):
    user = models.ForeignKey(TwitchUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    binded_to = ArrayField(base_field=models.CharField(max_length=20), default=list)
    has_cooldown = models.BooleanField(default=True)
    global_cooldown = models.IntegerField(default=10)
    user_cooldown = models.IntegerField(default=10)