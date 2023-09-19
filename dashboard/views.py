import json
import os
import requests

from itertools import chain

from dashboard.models import *
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.http import HttpRequest, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from .forms import UploadForm
from typing import Union


REWARD_CODES = ["songreq", "songskip", "chatgpt", "gptimage", "soundreq", "ytreq"]


# ======================================================================================================================
# VIEWS
# ======================================================================================================================


@never_cache
def index(request: HttpRequest):
    # If no user exists, redirect to home
    user = getUser(request.session.get('twitch_id', None))
    if not user:
        return HttpResponseRedirect(reverse('home'))
    
    # If the user isn't in the whitelist for smossbot, get em OUT
    if not username_exists(user.username) and user.username != "xzmozxx":
        return HttpResponseRedirect(reverse('gatekept'))
    
    twitch_credentials = user.twitchcredentials
    if not twitch_credentials:
        return HttpResponseRedirect(reverse('home'))
    
    # Validate their token to make sure we're still dealing with a valid access token.
    # Twitch requires this to be done hourly, but I'm just gonna do it every time. Not terribly efficient.
    # TODO: Find potential ways to make this better.
    valid = False
    required_scopes = os.getenv('TWITCH_SCOPE').split(' ')
    header = {
        'Authorization': "OAuth {}".format(twitch_credentials.access_token)
    }
    resp = requests.get("https://id.twitch.tv/oauth2/validate", headers=header)
    if resp.status_code == 200:
        # Let's also make sure they have the right scopes
        data = json.loads(resp.content.decode())
        valid = set(data['scopes']) == set(required_scopes)
    else:
        # Attempt a re-auth
        reauth_result = twitchReauth(user, twitch_credentials)
        valid = reauth_result['success'] and (set(twitch_credentials.scope) == set(required_scopes))

    # Clear out all Twitch-related stuff and boot them back to the home screen, if the token's expired or the reauth failed
    if not valid:
        request.session['twitch_id'] = None
        request.session['twitch_rewards'] = None
        for code in REWARD_CODES:
            if code + "_bind" in request.session:
                request.session[code + "_bind"] = None
        return HttpResponseRedirect(reverse('home'))

    # Get the user's custom rewards
    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(twitch_credentials.access_token)
    }
    resp = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards", params={'broadcaster_id': user.twitch_id}, headers=header)
    if resp.status_code == 403:
        # Refreshed API call tells us the user doesn't have channel points unlocked.
        request.session['twitch_rewards'] = "-1"
        # TODO-HIGH
        return HttpResponseNotFound("you dont have channel points")
    elif not 200 <= resp.status_code <= 226:
        return HttpResponseNotFound("Some error occured, idk what lmao. Error code: CRR{}".format(resp.status_code))

    data = json.loads(resp.content.decode())
    incoming_rewards = data['data']
    incoming_rewards_by_id = parse_rewards_using_id(incoming_rewards)
    known_rewards = ChannelPointReward.objects.filter(user=user)
    # Does this user have any rewards in the DB? If not, just write any incoming rewards to the DB
    if not known_rewards:
        # Do they even have rewards at all?
        if len(incoming_rewards) == 0:
            request.session['twitch_rewards'] = None
        else:
            known_rewards = [
                ChannelPointReward(
                    user = user,
                    reward_title = reward['title'],
                    reward_id = reward['id']
                ) for reward in incoming_rewards
            ]

            ChannelPointReward.objects.bulk_create(known_rewards)
            request.session['twitch_rewards'] = incoming_rewards_by_id

    # Database contains rewards at this point.
    # Does the cache know it?
    if not request.session.get('twitch_rewards', None):
        request.session['twitch_rewards'] = incoming_rewards_by_id

    # Cache has rewards in it, but are they up-to-date?
    # Check for new incoming rewards
    known_reward_ids = [reward.reward_id for reward in known_rewards]
    for incoming_reward_id, incoming_reward_data in incoming_rewards_by_id.items():
        if incoming_reward_id not in known_reward_ids:
            # Add the incoming reward data to DB and request.session
            incoming_reward = ChannelPointReward(
                reward_id = incoming_reward_data['id'],     # incoming_reward_id
                reward_title = incoming_reward_data['title'],
                user = user
            )
            incoming_reward.save()
    
    # Check for deleted rewards
    for known_reward_id in known_reward_ids:
        if known_reward_id not in incoming_rewards_by_id:
            known_rewards.get(reward_id=known_reward_id).delete()

    request.session['twitch_rewards'] = incoming_rewards_by_id
    
    # Build their vars
    buildUserVars(user)

    return render(request, "dashboard/index.html", context=buildContext(user))


# Someone clicks the "Bind Rewards" button
@never_cache
def bind(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured binding your channel point rewards.")
        return render(request, "dashboard/req_controller.html", context=buildContext(user))
    known_rewards = ChannelPointReward.objects.filter(user=user)

    # Gather info on the bindings user did
    reward_bindings = {}
    for code in REWARD_CODES:
        code_reward_id = request.GET.get(code, None)    # The reward_id associated with the channel point reward the user chose in the dropdown
        if code_reward_id is not None and code_reward_id != "null":   # Fuck you JS
            # Remove old bind in the database. Should only ever be one
            old_binded_reward = known_rewards.filter(binded_to__contains=[code]).first()
            if old_binded_reward is not None:
                old_binded_reward.binded_to.remove(code)
                old_binded_reward.save()
            # And store the new
            request.session[code + "_bind"] = code_reward_id
            if code_reward_id not in reward_bindings:   # reward_bindings{<reward_id ('123-abc-2nhrj2i1...')>: ['songreq', 'chatgpt']}
                reward_bindings[code_reward_id] = []    # One reward can be tied to multiple bindings. Should I change this? Probably.
            reward_bindings[code_reward_id].append(code)

    # And write the new bindings in the DB
    for reward_id, bindings in reward_bindings.items():
        reward = known_rewards.get(reward_id=reward_id)
        reward.binded_to = bindings
        reward.save()

    return render(request, "dashboard/req_controller.html", context=buildContext(user))


# Whenever a user clicks on trashcan icon to unbind a reward
@never_cache
def unbind(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured binding your channel point rewards.")
        return render(request, "dashboard/req_controller.html", context=buildContext(user))
    known_rewards = ChannelPointReward.objects.filter(user=user)
    code = request.GET.get("reward_code", None)

    # If it's created by us, then outright delete it from the DB and Twitch
    current_binded_reward = known_rewards.get(binded_to__contains=[code])
    if current_binded_reward.bot_created:
        header = {
            'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
            'Authorization': "Bearer {}".format(user.twitchcredentials.access_token)
        }
        params = {
            'broadcaster_id': user.twitch_id,
            'id': current_binded_reward.reward_id
        }
        resp = requests.delete(url="https://api.twitch.tv/helix/channel_points/custom_rewards", headers=header, params=params)
        if resp.status_code != 204:
            return
        current_binded_reward.delete()
    else:
        # Otherwise, just remove the bind
        current_binded_reward.binded_to.remove(code)
        current_binded_reward.save()

    # Clear it from cache
    request.session[code + "_bind"] = None

    return render(request, "dashboard/req_controller.html", context=buildContext(user))


# Whenever a channel point reward is created automatically by smossbot
@never_cache
def create(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured creating your channel point reward.")
        return render(request, "dashboard/req_controller.html", context=buildContext(user))
    known_rewards = ChannelPointReward.objects.filter(user=user)

    reward_name = request.POST.get("reward-name", None)
    description = request.POST.get("description", None)
    text_required = request.POST.get("text-required", None).lower().capitalize() == "True"
    cost = int(request.POST.get("cost", None))
    color = request.POST.get("color", None)
    # TODO-MEDIUM -- skipped rewards can't be refunded. Make this instead auto-accept and auto-refund? and not auto-accept always?
    # auto_skip = request.POST.get("auto-skip", None).lower().capitalize() == "True"
    auto_skip = False
    has_cooldown = request.POST.get("has-cooldown", None).lower().capitalize() == "True"
    cooldown_time = int(request.POST.get("cooldown-time", None))
    limit_per_stream = int(request.POST.get("cooldown-limit", None))
    user_limit_per_stream = int(request.POST.get("cooldown-userlimit", None))
    reward_code_id = request.POST.get("reward-code-id", None)

    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(user.twitchcredentials.access_token)
    }

    data = {
        'title': reward_name,
        'cost': cost,
        'prompt': description,
        'is_enabled': True,
        'background_color': color,
        'is_user_input_required': text_required,
        'should_redemptions_skip_request_queue': auto_skip
    }

    if has_cooldown:
        data.update({
            'is_max_per_stream_enabled': limit_per_stream != 0,
            'max_per_stream': limit_per_stream,
            'is_max_per_user_per_stream_enabled': user_limit_per_stream != 0,
            'max_per_user_per_stream': user_limit_per_stream,
            'is_global_cooldown_enabled': cooldown_time != 0,
            'global_cooldown_seconds': cooldown_time,
            'should_redemptions_skip_request_queue': auto_skip
        })

    resp = requests.post("https://api.twitch.tv/helix/channel_points/custom_rewards", headers=header, json=data, params={'broadcaster_id': user.twitch_id})
    if resp.status_code != 200:
        messages.add_message(request, messages.ERROR, "An error occured creating your channel point reward, from the Twitch API.")
        return render(request, "dashboard/req_controller.html", context=buildContext(user))
    data = json.loads(resp.content.decode())
    
    new_reward_data_resp = data['data'][0]
    new_reward_data = {
        'new_id': new_reward_data_resp['id'],
        'title': new_reward_data_resp['title']
    }

    # Unbind any reward_code_id binds currently in the DB
    old_bind = known_rewards.filter(binded_to__contains=[reward_code_id]).first()
    if old_bind is not None:
        old_bind.binded_to.remove(reward_code_id)
        old_bind.save()

    # And write the new one in
    new_reward = ChannelPointReward(
        reward_id = new_reward_data['new_id'],
        reward_title = new_reward_data['title'],
        user = user,
        bot_created = True,
        binded_to = [reward_code_id]
    )
    new_reward.save()
    
    # Cache it
    request.session[reward_code_id + '_bind'] = new_reward_data['new_id']

    # Update the cached lists of rewards
    if not request.session.get('twitch_rewards', None) is None:
        request.session['twitch_rewards'].update({
            new_reward_data['new_id']: new_reward_data_resp
        })

    return render(request, "dashboard/req_controller.html", context=buildContext(user))


@never_cache
def upload(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured, and you were signed out.")
        return HttpResponseRedirect(reverse('home'))
    
    if request.method == "POST":
        upload_form = UploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            doc = UploadedFile(
                file = request.FILES['file'],
                user = user,
                tag = request.POST['tag']
            )
            doc.save()
            messages.success(request, "Uploaded file successfully!")
            return HttpResponseRedirect(reverse('dashboard:upload'))
        else:
            errors = upload_form.errors.get_json_data()
            listed_errors = ''.join([fielddata[0]['message'] for fielddata in errors.values()])
            messages.error(request, "Error occured uploading: {}.".format(listed_errors))
    
    uploaded_files = UploadedFile.objects.filter(user=user).order_by('upload_date')
    max_uploads = False
    if len(uploaded_files) >= 10:
        max_uploads = True
    
    return render(request, "dashboard/upload.html", context=buildContext(user, {'form': UploadForm(), 'maxuploads': max_uploads, 'uploaded_files': uploaded_files}))


def changeTag(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured, and you were signed out.")
        return HttpResponseRedirect(reverse('home'))
    
    try:
        if request.method == "POST":
            new_tag = request.POST.get('newTagName', None)
            alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
            alphanumeric(new_tag)
            recipient = request.POST.get('hiddenFileID')
            file = UploadedFile.objects.filter(user=user, id=recipient).first()
            file.tag = new_tag
            file.save()
            messages.success(request, "Updated file tag successfully!")
    except ValidationError:
        messages.error(request, "Only alphanumeric characters are allowed.")

    return HttpResponseRedirect(reverse('dashboard:upload'))


def deleteFile(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured, and you were signed out.")
        return HttpResponseRedirect(reverse('home'))
    
    if request.method == "POST":
        recipient = request.POST.get('hiddenFileID')
        file = UploadedFile.objects.filter(user=user, id=recipient).first()
        file.delete()
        messages.success(request, "Deleted file successfully!")

    return HttpResponseRedirect(reverse('dashboard:upload'))


def deleteFiles(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if user is None:
        messages.add_message(request, messages.ERROR, "An error occured, and you were signed out.")
        return HttpResponseRedirect(reverse('home'))
    
    uploaded_files = UploadedFile.objects.filter(user=user)
    for file in uploaded_files:
        file.delete()

    messages.success(request, "All files successfully deleted.")
    return HttpResponseRedirect(reverse('dashboard:upload'))


def callAPI(request: HttpRequest):
    endpoint = request.GET.get("endpoint", None)
    divclass = request.GET.get("divclass", None)
    post_url = "{}{}".format(os.getenv('BACKEND_API'), endpoint)

    user = getUser(request.session['twitch_id'])

    data = {
        'user': user.username,
        'id': user.twitch_id
    }
    resp = requests.post(post_url, json=data)
    if not 200 <= resp.status_code <= 226:
        messages.add_message(request, messages.ERROR, "An error occured toggling your session.")
        return render(request, "dashboard/" + divclass + ".html", context=buildContext(user))
    resp_data = json.loads(resp.content.decode())

    return render(request, "dashboard/" + divclass + ".html", context=buildContext(user))


# DANGER ZONE
# Deletes user from the DB incase they want it.
def delete(request: HttpRequest):
    user = getUser(request.session.get('twitch_id', None))
    if not user:
        return HttpResponseRedirect(reverse('home'))
    
    # Disable their active session if they have it
    post_url = "{}end_endpoint".format(os.getenv('BACKEND_API'))
    data = {
        'user': user.username,
        'id': user.twitch_id
    }
    resp = requests.post(post_url, json=data)
    if not 200 <= resp.status_code <= 226:
        messages.add_message(request, messages.ERROR, "An error occured deleting your stuff; report this to me!")
        return HttpResponseRedirect(reverse('dashboard:index'))
    resp_data = json.loads(resp.content.decode())
    
    request.session['twitch_id'] = None
    request.session['twitch_rewards'] = None
    for code in REWARD_CODES:
        if code + "_bind" in request.session:
            request.session[code + "_bind"] = None

    user.delete()
    return HttpResponseRedirect(reverse('home'))


# ======================================================================================================================
# NON-VIEW FUNCTIONS
# ======================================================================================================================


def buildContext(user: TwitchUser, extra: dict = None) -> dict:
    user.refresh_from_db()

    try:
        twitch_authenticated = user.twitchcredentials is not None
    except TwitchUser.DoesNotExist:
        twitch_authenticated = None

    try:
        spotify_authenticated = user.spotifycredentials.code
        spotify_current = set(os.getenv('SPOTIFY_SCOPE').split(' ')).issubset(set(user.spotifycredentials.scope))
    except SpotifyCredentials.DoesNotExist:
        spotify_authenticated = None
        spotify_current = False

    fully_authenticated = twitch_authenticated and spotify_authenticated and spotify_current
    fully_authenticated_outdated = twitch_authenticated and spotify_authenticated and (not spotify_current)

    ctx = {
        'twitch_username': user.username,
        'superuser': user.username == "xzmozxx",
        'active_session': user.active_session,
        'twitch_authenticated': twitch_authenticated,
        'spotify_authenticated': spotify_authenticated,
        'spotify_current': spotify_current,
        'fully_authenticated': fully_authenticated,
        'fully_authenticated_outdated': fully_authenticated_outdated
    }

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

    ctx.update({
        'twitch_auth_url': twitch_auth_url,
        'spotify_auth_url': spotify_auth_url
    })

    all_rewards = ChannelPointReward.objects.filter(user=user)
    all_rewards_list = list(all_rewards.values())

    ctx.update({'twitch_rewards': all_rewards_list})

    reward_info = {}
    binded_rewards = all_rewards.filter(binded_to__isnull=False)
    binded_reward_codes = list(chain.from_iterable([reward.binded_to for reward in binded_rewards if reward.binded_to]))
    for code in REWARD_CODES:
        if code == "gptimage" and user.username != "xzmozxx":
            continue
        bind_info = {
            code: None
        }
        if code in binded_reward_codes:
            # TODO: why does `[code]` work and not `code` ???
            # https://docs.djangoproject.com/en/4.2/ref/models/querysets/#contains
            binded_reward = binded_rewards.filter(binded_to__contains=[code]).first()
            bind_info[code] = {
                'id': binded_reward.reward_id,
                'title': binded_reward.reward_title,
                'bot_created': binded_reward.bot_created
            }
        reward_info.update(bind_info)
    ctx.update({'reward_info': reward_info})

    if extra: ctx.update(extra)

    return ctx


# Builds the vars for the user.
# hasattr() will only ever return False once for every new user, or every new variable table.
def buildUserVars(user: TwitchUser) -> None:
    if not hasattr(user, 'songreqvars'):
        songreq_vars = SongReqVars(
            user = user
        )
        songreq_vars.save()
    if not hasattr(user, 'songskipvars'):
        songskip_vars = SongSkipVars(
            user = user
        )
        songskip_vars.save()
    if not hasattr(user, 'chatgptvars'):
        chatgpt_vars = ChatGPTVars(
            user = user
        )
        chatgpt_vars.save()
    if not hasattr(user, 'gptimagevars'):
        gptimage_vars = GPTImageVars(
            user = user
        )
        gptimage_vars.save()
    if not hasattr(user, 'ytreqvars'):
        ytreq_vars = YTReqVars(
            user = user
        )
        ytreq_vars.save()


# Refreshes the user's access token and saves the new credentials.
def twitchReauth(user: TwitchUser, twitch_credentials:TwitchCredentials = None) -> dict:
    if not twitch_credentials:
        twitch_credentials = user.twitchcredentials

    result = {
        'credentials': twitch_credentials,
        'success': False,
        'msg': "Twitch re-authentication was not successful."
    }

    header = {
        'Content-Type': "application/x-www-form-urlencoded"
    }
    params = {
        'client_id': os.getenv('TWITCH_CLIENT_ID'),
        'client_secret': os.getenv('TWITCH_CLIENT_SECRET'),
        'grant_type': "refresh_token",
        'refresh_token': twitch_credentials.refresh_token
    }
    resp = requests.post("https://id.twitch.tv/oauth2/token", headers=header, params=params)
    if not resp.ok:
        return result

    data = json.loads(resp.content.decode())
    result['success'] = True
    result['msg'] = "Twitch re-authentication was successful!"
    twitch_credentials.access_token = data['access_token']
    twitch_credentials.expires_in = data['expires_in']
    twitch_credentials.refresh_token = data['refresh_token']
    twitch_credentials.token_type = data['token_type']
    twitch_credentials.scope = data['scope']
    twitch_credentials.save()

    return result


def getUser(twitch_id) -> Union[TwitchUser, None]:
    return TwitchUser.objects.filter(twitch_id=twitch_id).first()


def getTwitchCredentials(user: TwitchUser) -> dict:
    twitch_data = {
        'code': user.twitchcredentials.code,
        'access_token': user.twitchcredentials.access_token,
        'token_type': user.twitchcredentials.token_type,
        'expires_in': user.twitchcredentials.expires_in,
        'refresh_token': user.twitchcredentials.refresh_token,
        'scope': user.twitchcredentials.scope
    }
    return twitch_data


def getSpotifyCredentials(user: TwitchUser) -> dict:
    spotify_data = {
        'code': user.spotifycredentials.code,
        'access_token': user.spotifycredentials.access_token,
        'token_type': user.spotifycredentials.token_type,
        'expires_in': user.spotifycredentials.expires_in,
        'refresh_token': user.spotifycredentials.refresh_token
    }
    return spotify_data


def username_exists(username):
    return User.objects.filter(username=username.lower()).exists()


def parse_rewards(rewards_data) -> dict:
    parsed = {}
    for reward in rewards_data:
        parsed[reward['title']] = reward['id']
    return parsed


def parse_rewards_using_id(rewards_data) -> dict:
    parsed = {}
    for reward in rewards_data:
        parsed[reward['id']] = reward
    return parsed

def log(output):
    print("[{}] {}".format(datetime.now(), output))