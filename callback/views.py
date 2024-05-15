from accounts.models import TwitchUser, TwitchCredentials, SpotifyCredentials
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from typing import Union
from utils import users
from utils.spotify import api as SpotifyAPI
from utils.twitch import api as TwitchAPI


# Entry point for the dashboard from someone signing in. Twitch URI redirects to here
def twitch(request: HttpRequest):
    # code is gotten from the Twitch Sign-in Button
    twitch_code = request.GET.get('code')

    if twitch_code is None:
        messages.add_message(request, messages.ERROR, "An error occured signing into Twitch; no code was returned.")
        return HttpResponseRedirect(reverse('home'))

    token_result = TwitchAPI.getToken(twitch_code)
    if not token_result['ok']:
        messages.add_message(request, messages.ERROR, token_result['msg'])
        return HttpResponseRedirect(reverse('home'))

    auth_data = token_result['credentials']
    user = authenticate(request, token=auth_data['access_token'])
    # Sanity check
    if user is None:
        return HttpResponseRedirect(reverse('home'))

    login(request, user)
    users.buildUserVars(user)
    twitch_credentials = TwitchCredentials(
        user = user,
        code = twitch_code,
        access_token = auth_data['access_token'],
        expires_in = auth_data['expires_in'],
        refresh_token = auth_data['refresh_token'],
        token_type = auth_data['token_type'],
        scope = auth_data['scope']
    )
    twitch_credentials.save()
    
    return HttpResponseRedirect(reverse('dashboard:index'))


# Spotify URI redirects to here
def spotify(request: HttpRequest):
    user = request.user
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured signing into Spotify; no user exists.")
        return HttpResponseRedirect(reverse('home'))

    spotify_code = request.GET.get('code')
    if spotify_code is None:
        messages.add_message(request, messages.ERROR, "An error occured signing into Spotify; no code was returned.")
        return HttpResponseRedirect(reverse('dashboard:index'))
    
    token_result = SpotifyAPI.getToken(spotify_code)
    if not token_result['ok']:
        messages.add_message(request, messages.ERROR, token_result['msg'])
        return HttpResponseRedirect(reverse('dashboard:index'))

    auth_data = token_result['credentials']
    spotify_credentials = SpotifyCredentials(
        user = user,
        code = spotify_code,
        access_token = auth_data['access_token'],
        expires_in = auth_data['expires_in'],
        refresh_token = auth_data['refresh_token'],
        token_type = auth_data['token_type'],
        scope = auth_data['scope'].split(' ')
    )
    spotify_credentials.save()

    return HttpResponseRedirect(reverse('dashboard:index'))


def getUser(twitch_id) -> Union[TwitchUser, None]:
    return TwitchUser.objects.filter(twitch_id=twitch_id).first()