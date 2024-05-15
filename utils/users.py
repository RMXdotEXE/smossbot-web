import json
import os
import requests

from itertools import chain

from accounts.models import TwitchUser
from bot.models import *    # Vars
from dashboard.models import *
from django.contrib.auth import logout
from django.http import HttpRequest
from typing import Union
from utils.twitch import api as TwitchAPI


def getUser(twitch_id:int) -> Union[TwitchUser, None]:
    """
    Gets the TwitchUser associated with the given twitch_id, or None
    if there's nobody associated with twitch_id.
    """
    if twitch_id is None: return None
    
    return TwitchUser.objects.filter(twitch_id=twitch_id).first()


def userIsWhitelisted(twitch_username:str) -> bool:
    """
    Determines whether the user is on a whitelist or not for access to
    smossbot, and other things.
    """
    return TwitchUser.objects.filter(username=twitch_username.lower()).exists()


def getTwitchRewards(twitch_id:int) -> Union[dict, None]:
    """
    Gets the channel points associated with twitch_id.
    Returns the channel point rewards as a dict, or None if none exist.
    """
    user = getUser(twitch_id)
    reward_request = TwitchAPI.getCustomRewards(twitch_id, user.twitchcredentials.access_token)
    incoming_rewards = None
    if reward_request['ok']:
        incoming_rewards = reward_request['data']
    return incoming_rewards


def buildUserVars(user:TwitchUser) -> None:
    """
    Sets up the variables for a user's functions, as seen under the "Commands" page.
    """
    if not hasattr(user, 'songreqvars'):
        songreq_vars = SongReqVars(
            user = user
        )
        songreq_vars.save()
    if not hasattr(user, 'songskipvars'):
        songskip_vars = SongSkipVars(
            user = user
        )
        songskip_vars.save()
    if not hasattr(user, 'chatgptvars'):
        chatgpt_vars = ChatGPTVars(
            user = user
        )
        chatgpt_vars.save()
    if not hasattr(user, 'gptimagevars'):
        gptimage_vars = GPTImageVars(
            user = user
        )
        gptimage_vars.save()
    if not hasattr(user, 'ytreqvars'):
        ytreq_vars = YTReqVars(
            user = user
        )
        ytreq_vars.save()
    return


def deleteUser(request: HttpRequest) -> bool:
    """
    Deletes information about the user, from smossbot.
    This function is called if the user wants to remove all information and
    affiliation with the bot.
    Returns bool indicating status.
    """
    # Disable their active session if they have it
    post_url = "{}session".format(os.getenv('BACKEND_API'))
    data = {
        'user': request.user.username,
        'id': request.user.twitch_id,
        'session': False
    }
    resp = requests.post(post_url, json=data)
    if not 200 <= resp.status_code <= 226:
        return False

    request.user.delete()
    logout(request)
    
    return True