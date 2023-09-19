import base64
import json
import os

import requests

from dashboard.models import *
from django.contrib import messages
from django.http import HttpRequest, HttpResponseRedirect, HttpResponseNotFound
from django.urls import reverse
from typing import Union


# Entry point for the dashboard from someone signing in. Twitch URI redirects to here
def twitch(request: HttpRequest):
    # code is gotten from the Twitch Sign-in Button
    twitch_code = request.GET.get('code')

    if twitch_code is None:
        messages.add_message(request, messages.ERROR, "An error occured signing into Twitch; no code was returned.")
        return HttpResponseRedirect(reverse('home'))

    # Get OAuth credentials from this user
    params = {
        'client_id': os.getenv('TWITCH_CLIENT_ID'),
        'client_secret': os.getenv('TWITCH_CLIENT_SECRET'),
        'code': twitch_code,
        'grant_type': 'authorization_code',
        'redirect_uri': os.getenv('TWITCH_REDIRECT_URI')
    }
    resp = requests.post("https://id.twitch.tv/oauth2/token", params=params)
    if not 200 <= resp.status_code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 2A{}".format(resp.status_code))
    auth_data = json.loads(resp.content.decode())

    # With the authorization code given, now we grab information about the user (their username, ID, and broadcaster type).
    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(auth_data['access_token'])
    }
    resp = requests.get("https://api.twitch.tv/helix/users", headers=header)
    if not 200 <= resp.status_code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 3A{}".format(resp.status_code))
    user_data = json.loads(resp.content.decode())
    user_id = user_data['data'][0]['id']

    # Write to DB if they're a new user
    user = getUser(user_id)
    if user is None:
        user = TwitchUser(
            twitch_id = user_data['data'][0]['id'],
            username = user_data['data'][0]['login']
        )
    twitch_credentials = TwitchCredentials(
        user = user,
        code = twitch_code,
        access_token = auth_data['access_token'],
        expires_in = auth_data['expires_in'],
        refresh_token = auth_data['refresh_token'],
        token_type = auth_data['token_type'],
        scope = auth_data['scope']
    )
    user.save()
    twitch_credentials.save()

    request.session['twitch_id'] = user.twitch_id
    
    return HttpResponseRedirect(reverse('dashboard:index'))


# Spotify URI redirects to here
def spotify(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured signing into Spotify; no user exists.")
        return HttpResponseRedirect(reverse('home'))

    spotify_code = request.GET.get('code')
    if spotify_code is None:
        messages.add_message(request, messages.ERROR, "An error occured signing into Spotify; no code was returned.")
        return HttpResponseRedirect(reverse('dashboard:index'))

    auth_str = "{}:{}".format(os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET'))
    encoded_str = base64.urlsafe_b64encode(auth_str.encode()).decode()

    header = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': "Basic {}".format(encoded_str)
    }
    params = {
        'grant_type': 'authorization_code',
        'code': spotify_code,
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI')
    }

    resp = requests.post("https://accounts.spotify.com/api/token", params=params, headers=header)
    if not 200 <= resp.status_code <= 226:
        messages.add_message(request, messages.ERROR, "An error occured signing into Spotify; grabbing authorization token was unsuccessful.")
        return HttpResponseRedirect(reverse('dashboard:index'))
    resp_data = json.loads(resp.content.decode())

    # Write to DB
    spotify_credentials = SpotifyCredentials(
        user = user,
        code = spotify_code,
        access_token = resp_data['access_token'],
        expires_in = resp_data['expires_in'],
        refresh_token = resp_data['refresh_token'],
        token_type = resp_data['token_type'],
        scope = resp_data['scope'].split(' ')
    )
    spotify_credentials.save()

    return HttpResponseRedirect(reverse('dashboard:index'))


def getUser(twitch_id) -> Union[TwitchUser, None]:
    return TwitchUser.objects.filter(twitch_id=twitch_id).first()