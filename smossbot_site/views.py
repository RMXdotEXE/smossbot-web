import os
import requests

from django.shortcuts import render


def home(request):
    return render(request, "home.html", context=build_ctx(request))


def gatekept(request):
    return render(request, "gatekept.html", context=build_ctx(request))


def commands(request):
    return render(request, "commands.html", context=build_ctx(request))


def changelog(request):
    return render(request, "changelog.html", context=build_ctx(request))


def login_check(_request):
    valid = False
    header = {
        'Authorization': "OAuth {}".format(_request.session.get('twitch_access_token', None))
    }
    rawsp = requests.get("https://id.twitch.tv/oauth2/validate", headers=header)
    code = rawsp.status_code
    if 200 <= code <= 226: valid = True
    if not valid:
        # Clear out all Twitch-related stuff and boot them back to the home screen
        _request.session['twitch_username'] = None
        _request.session['twitch_access_token'] = None
        _request.session['twitch_expires_in'] = None
        _request.session['twitch_refresh_token'] = None
        _request.session['twitch_token_type'] = None
    return valid


def build_ctx(_request):
    ctx = None
    if not login_check(_request):
        ctx = {'twitch_auth_url': create_twitch_auth_url()}
    else:
        ctx = get_twitch_context(_request)
    return ctx


def get_twitch_context(_request):
    return {'twitch_username': _request.session.get('twitch_username', None)}


def create_twitch_auth_url():
    twitch_auth_url = "https://id.twitch.tv/oauth2/authorize?" + \
        "client_id=" + os.getenv('TWITCH_CLIENT_ID') + \
        "&redirect_uri=" + os.getenv('TWITCH_REDIRECT_URI') + \
        "&response_type=code" + \
        "&scope=" + os.getenv('TWITCH_SCOPE')
    return twitch_auth_url