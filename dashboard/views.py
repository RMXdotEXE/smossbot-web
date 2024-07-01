import os

from accounts.models import TwitchUser
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from functions.models import ChannelPointReward, CommandFunction
from itertools import chain
from utils import views
from utils.users import deleteUser


# ======================================================================================================================
# VIEWS
# ======================================================================================================================
@never_cache
@views.twitchRequired
def index(request: HttpRequest):
    user = request.user

    # If the user isn't in the whitelist for smossbot, give em the L
    if not username_exists(user.username) and user.username != "xzmozxx":
        return HttpResponseRedirect(reverse('gatekept'))
    
    twitch_credentials = user.twitchcredentials
    if not twitch_credentials:
        return HttpResponseRedirect(reverse('home'))

    ctx = views.buildBaseContext(user)
    ctx.update(buildContext(user))

    return render(request, "dashboard/index.html", context=ctx)


@views.twitchRequired
def delete(request: HttpRequest):
    result = deleteUser(request)
    print(result)
    return HttpResponseRedirect(reverse('home'))


# ======================================================================================================================
# NON-VIEW FUNCTIONS
# ======================================================================================================================
def buildContext(user: TwitchUser) -> dict:
    user.refresh_from_db()

    try:
        twitch_authenticated = user.twitchcredentials is not None
    except TwitchUser.DoesNotExist:
        twitch_authenticated = None

    user_reward_binds = ChannelPointReward.objects.filter(user=user)
    user_command_binds = CommandFunction.objects.filter(user=user)

    # TODO-LOW: There's gotta be a better way right?
    songreq_binded = len(user_reward_binds.filter(user=user, binded_to__contains=["songreq"])) + len(user_command_binds.filter(user=user, binded_to__contains=["songreq"])) != 0
    ytreq_binded = len(user_reward_binds.filter(user=user, binded_to__contains=["ytreq"])) + len(user_command_binds.filter(user=user, binded_to__contains=["ytreq"])) != 0
    soundreq_binded = len(user_reward_binds.filter(user=user, binded_to__contains=["soundreq"])) + len(user_command_binds.filter(user=user, binded_to__contains=["soundreq"])) != 0

    ctx = {
        'active_session': user.active_session,
        'twitch_authenticated': twitch_authenticated,
        'songreq_binded': songreq_binded,
        'ytreq_binded': ytreq_binded,
        'soundreq_binded': soundreq_binded
    }

    return ctx


def username_exists(username):
    return TwitchUser.objects.filter(username=username.lower()).exists()