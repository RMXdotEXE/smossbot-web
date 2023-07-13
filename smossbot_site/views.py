import os
import requests

from dashboard.models import TwitchUser
from django.shortcuts import render
from typing import Union


def home(request):
    return render(request, "home.html", context=build_ctx(request))


def gatekept(request):
    return render(request, "gatekept.html", context=build_ctx(request))


def commands(request):
    return render(request, "commands.html", context=build_ctx(request))


def changelog(request):
    return render(request, "changelog.html", context=build_ctx(request))


def build_ctx(_request):
    ctx = None

    user = getUser(_request.session.get('twitch_id', None))
    if not user or not login_still_valid(user):
        ctx = {'twitch_auth_url': create_twitch_auth_url()}
        _request.session['twitch_id'] = None
        _request.session['twitch_rewards'] = None
        for code in ["songreq", "chatgpt", "songskip", "ytreq"]:
            if code + "_bind" in _request.session:
                _request.session[code + "_bind"] = None
    else:
        ctx = {'twitch_username': user.username}
    return ctx


def create_twitch_auth_url():
    twitch_auth_url = "https://id.twitch.tv/oauth2/authorize?" + \
        "client_id=" + os.getenv('TWITCH_CLIENT_ID') + \
        "&redirect_uri=" + os.getenv('TWITCH_REDIRECT_URI') + \
        "&response_type=code" + \
        "&scope=" + os.getenv('TWITCH_SCOPE')
    return twitch_auth_url


def getUser(twitch_id) -> Union[TwitchUser, None]:
    return TwitchUser.objects.filter(twitch_id=twitch_id).first()


def login_still_valid(user: TwitchUser) -> bool:
    header = {
        'Authorization': "OAuth {}".format(user.twitchcredentials.access_token)
    }
    resp = requests.get("https://id.twitch.tv/oauth2/validate", headers=header)
    if 200 <= resp.status_code <= 226:
        return True
    else:
        return False