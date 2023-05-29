import base64
import json
import os
import requests

from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.urls import reverse

def username_exists(username):
    return User.objects.filter(username=username.lower()).exists()

def index(request):
    user = request.session.get('twitch_username', None)
    if user is None:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: U404")

    # If the user isn't in the whitelist for smossbot, get em OUT
    if not username_exists(user):
        return HttpResponseRedirect(reverse('gatekept'))
    
    # If this user is not yet registered in the backend, then do so.
    # Session is not active by default.
    # If they ARE registered, assert this to the browser.
    r = requests.get(os.getenv('BACKEND_API') + "users")
    if not (200 <= r.status_code <= 226):
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: AA{}".format(r.status_code))
    resp = json.loads(r.content.decode())
    users = resp.get('users')
    registered = user in users
    if not registered:
        r = requests.post(os.getenv('BACKEND_API'), json=bundleData(request))
        if 200 <= r.status_code <= 226:
            resp = json.loads(r.content.decode())
            request.session['registered'] = resp.get('registered', False)
            request.session['active_session'] = resp.get('active_session', False)
        else:
            return HttpResponseNotFound("Some error occured, idk what lmao. Error code: B{}".format(r.status_code))
    else:
        request.session['registered'] = True

    # Prepare the template, and return it once it's done.
    # Do we really need twitch stuffs?
    twitch_auth_url = "https://id.twitch.tv/oauth2/authorize?" + \
        "client_id=" + os.getenv('TWITCH_CLIENT_ID') + \
        "&redirect_uri=" + os.getenv('TWITCH_REDIRECT_URI') + \
        "&response_type=code" + \
        "&scope=" + os.getenv('TWITCH_SCOPE')

    spotify_auth_url = "https://accounts.spotify.com/authorize?" + \
        "client_id=" + os.getenv('SPOTIFY_CLIENT_ID') + \
        "&response_type=code" + \
        "&redirect_uri=" + os.getenv('SPOTIFY_REDIRECT_URI') + \
        "&scope=" + os.getenv('SPOTIFY_SCOPE')

    ctx = {
        'user': request.user,
        'superuser': request.user.is_superuser,
        'twitch_auth_url': twitch_auth_url,
        'spotify_auth_url': spotify_auth_url,
        'twitch_code': request.session.get('twitch_code', None),
        'spotify_code': request.session.get('spotify_code', None),
        'custom_rewards': request.session.get('twitch_rewards_data', None),
        'songreq_reward': request.session.get('songreq_reward', None),
        'songreq_reward_title': request.session.get('songreq_reward_title', None),
        'chatgpt_reward': request.session.get('chatgpt_reward', None),
        'chatgpt_reward_title': request.session.get('chatgpt_reward_title', None),
        'registered': request.session.get('registered', False),
        'active_session': request.session.get('active_session', False),
        'twitch_username': request.session.get('twitch_username', None),
        'backend_api': os.environ.get('BACKEND_API'),
        'backend_on': request.session.get('backend_on', False),
    }

    return render(request, "dashboard/index.html", context=ctx)


def twitch(request):
    twitch_code = request.GET.get('code')
    if twitch_code is not None:
        request.session['twitch_code'] = twitch_code

        params = {
            'client_id': os.getenv('TWITCH_CLIENT_ID'),
            'client_secret': os.getenv('TWITCH_CLIENT_SECRET'),
            'code': twitch_code,
            'grant_type': 'authorization_code',
            'redirect_uri': os.getenv('TWITCH_REDIRECT_URI')
        }

        r = requests.post("https://id.twitch.tv/oauth2/token", params=params)
        resp = json.loads(r.content.decode())

        if not 200 <= r.status_code <= 226:
            return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 1A{}".format(code))

        request.session['twitch_access_token'] = resp['access_token']
        request.session['twitch_expires_in'] = resp['expires_in']
        request.session['twitch_refresh_token'] = resp['refresh_token']
        request.session['twitch_token_type'] = resp['token_type']
    else:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 2A{}".format(code))

    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(request.session['twitch_access_token'])
    }
    resp = requests.get("https://api.twitch.tv/helix/users", headers=header)
    code = resp.status_code
    if not 200 <= code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 3A{}".format(code))

    r = resp.content.decode()
    r = json.loads(r)

    username = r['data'][0]['login']
    id = r['data'][0]['id']

    request.session['twitch_username'] = username
    request.session['twitch_id'] = id

    resp = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards", params={'broadcaster_id': id}, headers=header)
    code = resp.status_code
    if not 200 <= code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 4A{}".format(code))

    r = resp.content.decode()
    r = json.loads(r)

    request.session['twitch_rewards_data'] = parse_rewards(r['data'])

    return HttpResponseRedirect(reverse('dashboard:index'))


def spotify(request):
    spotify_code = request.GET.get('code')
    if spotify_code is not None:
        request.session['spotify_code'] = spotify_code

        auth_str = "{}:{}".format(os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET'))
        encoded_str = base64.urlsafe_b64encode(auth_str.encode()).decode()

        header = {'Content-Type': "application/x-www-form-urlencoded",
            'Authorization': "Basic {}".format(encoded_str)}

        params = {
            'grant_type': 'authorization_code',
            'code': spotify_code,
            'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI')
        }

        r = requests.post("https://accounts.spotify.com/api/token", params=params, headers=header)
        resp = json.loads(r.content.decode())

        request.session['spotify_access_token'] = resp['access_token']
        request.session['spotify_token_type'] = resp['token_type']
        request.session['spotify_expires_in'] = resp['expires_in']
        request.session['spotify_refresh_token'] = resp['refresh_token']

        r = requests.post(os.getenv('BACKEND_API') + "set_data", json=bundleSpotifyData(request))
        if not 200 <= r.status_code <= 226:
            return HttpResponseNotFound("Some error occured, idk what lmao. Error code: bind{}\n".format(r.status_code))

    return HttpResponseRedirect(reverse('dashboard:index'))


def callAPI(request):
    endpoint = request.GET.get("endpoint", None)
    divclass = request.GET.get("divclass", None)
    post_url = "{}{}".format(os.getenv('BACKEND_API'), endpoint)
    rawsponse = requests.post(post_url, json={'user': request.session['twitch_username']})
    if not 200 <= rawsponse.status_code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: command{}\nReport this to me!!".format(rawsponse.status_code))
    resp = json.loads(rawsponse.content.decode())
    request.session['active_session'] = resp.get('active_session', False)

    ctx = {
        'active_session': request.session['active_session'],
    }

    return render(request, "dashboard/" + divclass + ".html", context=ctx)


def bind(request):
    songreq_id = request.GET.get("songreq_id", None)
    if songreq_id is not None and songreq_id != "-1" and songreq_id != "undefined":
        request.session['songreq_reward'] = songreq_id
        request.session['songreq_reward_title'] = [k for k, v in request.session['twitch_rewards_data'].items() if v == songreq_id][0]

    chatgpt_id = request.GET.get("chatgpt_id", None)
    if chatgpt_id is not None and chatgpt_id != "-1":
        request.session['chatgpt_reward'] = chatgpt_id
        request.session['chatgpt_reward_title'] = [k for k, v in request.session['twitch_rewards_data'].items() if v == chatgpt_id][0]

    r = requests.post(os.getenv('BACKEND_API') + "set_data", json=bundleRewardData(request))
    if not 200 <= r.status_code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: bind{}\n".format(r.status_code))

    ctx = {
        'spotify_code': request.session.get('spotify_code', None),
        'custom_rewards': request.session.get('twitch_rewards_data', None),
        'songreq_reward': request.session.get('songreq_reward', None),
        'songreq_reward_title': request.session.get('songreq_reward_title', None),
        'chatgpt_reward': request.session.get('chatgpt_reward', None),
        'chatgpt_reward_title': request.session.get('chatgpt_reward_title', None)
    }
    
    return render(request, "dashboard/req_controller.html", context=ctx)





def bundleData(_request):
    twitch_data = {
        'code': _request.session['twitch_code'],
        'access_token': _request.session['twitch_access_token'],
        'expires_in': _request.session['twitch_expires_in'],
        'refresh_token': _request.session['twitch_refresh_token'],
        'token_type': _request.session['twitch_token_type'],
    }

    spotify_data = {
        'code': _request.session.get('spotify_code', None),
        'access_token': _request.session.get('spotify_access_token', None),
        'token_type': _request.session.get('spotify_token_type', None),
        'expires_in': _request.session.get('spotify_expires_in', None),
        'refresh_token': _request.session.get('spotify_refresh_token', None),
    }

    reward_data = {
        'songreq_id': _request.session.get('songreq_reward', None),
        'chatgpt_id': _request.session.get('chatgpt_reward', None),
    }

    data = {
        'username': _request.session['twitch_username'],
        'twitch_data': twitch_data,
        'spotify_data': spotify_data,
        'reward_data': reward_data,
    }

    return data



def bundleSpotifyData(_request):
    spotify_data = {
        'code': _request.session.get('spotify_code', None),
        'access_token': _request.session.get('spotify_access_token', None),
        'token_type': _request.session.get('spotify_token_type', None),
        'expires_in': _request.session.get('spotify_expires_in', None),
        'refresh_token': _request.session.get('spotify_refresh_token', None),
    }

    data = {
        'username': _request.session['twitch_username'],
        'spotify_data': spotify_data,
        'type': "spotify_data",
    }

    return data


def bundleRewardData(_request):
    reward_data = {
        'songreq_id': _request.session.get('songreq_reward', None),
        'chatgpt_id': _request.session.get('chatgpt_reward', None),
    }

    data = {
        'username': _request.session['twitch_username'],
        'reward_data': reward_data,
        'type': "reward_data",
    }

    return data


def parse_rewards(rewards_data):
    parsed = {}
    for reward in rewards_data:
        parsed[reward['title']] = reward['id']
    return parsed