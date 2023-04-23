import os

from django.shortcuts import render

def home(request):
    twitch_auth_url = "https://id.twitch.tv/oauth2/authorize?" + \
        "client_id=" + os.getenv('TWITCH_CLIENT_ID') + \
        "&redirect_uri=" + os.getenv('TWITCH_REDIRECT_URI') + \
        "&response_type=code" + \
        "&scope=" + os.getenv('TWITCH_SCOPE')
    
    twitch_username = request.session.get('twitch_username', None)

    ctx = {
        'twitch_auth_url': twitch_auth_url,
        'twitch_username': twitch_username
    }

    return render(request, "home.html", context=ctx)

def gatekept(request):
    return render(request, "gatekept.html", context={'twitch_username': request.session.get('twitch_username', 'user')})