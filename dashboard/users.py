import json
import os
import requests

from itertools import chain

from accounts.models import TwitchUser
from dashboard.models import *
from datetime import datetime
from accounts.models import TwitchUser
from django.core.validators import RegexValidator
from typing import Union


def getUser(twitch_id:int) -> Union[TwitchUser, None]:
    """
    Gets the TwitchUser associated with the given twitch_id, or None
    if there's nobody associated with twitch_id.
    """
    return TwitchUser.objects.filter(twitch_id=twitch_id).first()


def userIsWhitelisted(twitch_username:str) -> bool:
    """
    Determines whether the user is on a whitelist or not for access to
    smossbot, and other things.
    """
    return TwitchUser.objects.filter(username=twitch_username.lower()).exists()