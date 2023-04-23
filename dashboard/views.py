import base64
import json
import os
import requests

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse

def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

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

<<<<<<< HEAD
=======
        if not 200 <= r.status_code <= 226:
            return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 1A{}".format(code))

>>>>>>> bedb12cd88b1ab3f8158ae175c0e39b75fa28dfd
        request.session['twitch_access_token'] = resp['access_token']
        request.session['twitch_expires_in'] = resp['expires_in']
        request.session['twitch_refresh_token'] = resp['refresh_token']
        request.session['twitch_token_type'] = resp['token_type']
<<<<<<< HEAD
=======
    else:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 2A{}".format(code))
>>>>>>> bedb12cd88b1ab3f8158ae175c0e39b75fa28dfd

    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(request.session['twitch_access_token'])
    }
    resp = requests.get("https://api.twitch.tv/helix/users", headers=header)
    code = resp.status_code
    if not 200 <= code <= 226:
<<<<<<< HEAD
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 1A{}".format(code))
=======
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 3A{}".format(code))
>>>>>>> bedb12cd88b1ab3f8158ae175c0e39b75fa28dfd

    r = resp.content.decode()
    r = json.loads(r)

    username = r['data'][0]['login']
    id = r['data'][0]['id']

    request.session['twitch_username'] = username
    request.session['twitch_id'] = id

    resp = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards", params={'broadcaster_id': id}, headers=header)
    code = resp.status_code
    if not 200 <= code <= 226:
<<<<<<< HEAD
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 2A{}".format(code))
=======
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: 4A{}".format(code))
>>>>>>> bedb12cd88b1ab3f8158ae175c0e39b75fa28dfd

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

    return HttpResponseRedirect(reverse('dashboard:index'))


def send_data(request):
    twitch_data = {
        'code': request.session['twitch_code'],
        'access_token': request.session['twitch_access_token'],
        'expires_in': request.session['twitch_expires_in'],
        'refresh_token': request.session['twitch_refresh_token'],
        'token_type': request.session['twitch_token_type'],
    }

    spotify_data = {
        'code': request.session.get('spotify_code', None),
        'access_token': request.session.get('spotify_access_token', None),
        'token_type': request.session.get('spotify_token_type', None),
        'expires_in': request.session.get('spotify_expires_in', None),
        'refresh_token': request.session.get('spotify_refresh_token', None),
    }

    reward_data = {
        'songreq_id': request.session.get('songreq_reward', None),
        'chatgpt_id': request.session.get('chatgpt_reward', None),
    }

    data = {
        'username': request.session['twitch_username'],
        'twitch_data': twitch_data,
        'spotify_data': spotify_data,
        'reward_data': reward_data,
    }

    r = requests.post(os.getenv('BACKEND_API'), json=data)
    if 200 <= r.status_code <= 226:
        resp = json.loads(r.content.decode())
        request.session['registered'] = resp.get('registered', False)
        request.session['active_session'] = resp.get('active_session', False)
        return HttpResponseRedirect(reverse('dashboard:index'))
    else:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: B{}".format(r.status_code))


def after_auth(request):
    command = request.POST.get("command")
    post_url = "{}{}".format(os.getenv('BACKEND_API'), command)
    r = requests.post(post_url, json={'user': request.session['twitch_username']})
    if not 200 <= r.status_code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: command{}\nReport this to me!!".format(r.status_code))
    resp = json.loads(r.content.decode())
    request.session['active_session'] = resp.get('active_session' or False)
    request.session['backend_on'] = resp.get('backend_on' or False)
    return HttpResponseRedirect(reverse('dashboard:index'))


def bind(request):
    section = request.POST.get("section")
    if section == "songreq":
        id = request.POST.get("songreq_id")
        request.session['songreq_reward'] = id
        request.session['songreq_reward_title'] = [k for k, v in request.session['twitch_rewards_data'].items() if v == id][0]
    elif section == "chatgpt":
        id = request.POST.get("chatgpt_id")
        request.session['chatgpt_reward'] = id
        request.session['chatgpt_reward_title'] = [k for k, v in request.session['twitch_rewards_data'].items() if v == id][0]
    
    return HttpResponseRedirect(reverse('dashboard:index'))


def parse_rewards(rewards_data):
    parsed = {}
    for reward in rewards_data:
        parsed[reward['title']] = reward['id']
    return parsed