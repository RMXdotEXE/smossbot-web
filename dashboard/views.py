import os

from accounts.models import TwitchUser
from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
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

    ctx = {
        'active_session': user.active_session,
        'twitch_authenticated': twitch_authenticated,
        'overlay_link': "{}{}{}".format(os.getenv("HOST_URL"), "/overlay/", user.username)
    }

    return ctx


def username_exists(username):
    return TwitchUser.objects.filter(username=username.lower()).exists()