import os

from accounts.models import TwitchUser, SpotifyCredentials
from django.contrib.auth import logout
from django.urls import reverse
from django.http import HttpRequest, HttpResponseRedirect
from utils.auth import buildTwitchAuthURL, validateUser


REWARD_CODES = ["songreq", "songskip", "chatgpt", "gptimage", "soundreq", "ytreq"]


def twitchRequired(view):
    """
    Decorator for a view to make sure that a user currently exists in the session, has
    Twitch credentials, and has a valid Twitch token.
    Returns them to the home screen and logs them out if something's up, and lets the
    view function as normal otherwise.
    """
    def wrapper(request: HttpRequest):
        user = request.user
        if not user \
        or not user.is_authenticated \
        or not user.twitchcredentials \
        or not validateUser(user)['ok']:
            logout(request)
            return HttpResponseRedirect(reverse('home'))
        return view(request)
    return wrapper


def buildBaseContext(user: TwitchUser) -> dict:
    """
    Builds and returns base context. Base context either has a twitch_auth_url if
    the user has no valid credentials, or their twitch_username if they're valid.
    """
    ctx = {}
    if not user.is_authenticated or not validateUser(user)['ok']:
        ctx = {'twitch_auth_url': buildTwitchAuthURL()}
        return ctx
    
    ctx = {
        'twitch_username': user.username,
        'superuser': user.username == "xzmozxx",
        'is_affiliate': user.is_affiliate
    }

    user.refresh_from_db()

    try:
        spotify_authenticated = user.spotifycredentials.code is not None
        spotify_current = set(os.getenv('SPOTIFY_SCOPE').split(' ')).issubset(set(user.spotifycredentials.scope))
    except SpotifyCredentials.DoesNotExist:
        spotify_authenticated = False
        spotify_current = False

    if not spotify_current:
        spotify_auth_url = "https://accounts.spotify.com/authorize?" + \
            "client_id=" + os.getenv('SPOTIFY_CLIENT_ID') + \
            "&response_type=code" + \
            "&redirect_uri=" + os.getenv('SPOTIFY_REDIRECT_URI') + \
            "&scope=" + os.getenv('SPOTIFY_SCOPE')
        ctx.update({
            'spotify_auth_url': spotify_auth_url
        })

    fully_authenticated = spotify_authenticated and spotify_current
    fully_authenticated_outdated = spotify_authenticated and not spotify_current

    ctx.update({
        'spotify_authenticated': spotify_authenticated,
        'spotify_current': spotify_current,
        'fully_authenticated': fully_authenticated,
        'fully_authenticated_outdated': fully_authenticated_outdated
    })

    return ctx


def isAjax(_request) -> bool:
  """
  Detects if the request was made using Ajax as opposed to a regular request.
  Returns True if so, and False if not.
  """
  return _request.headers.get('x-requested-with') == "XMLHttpRequest"