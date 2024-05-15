import json
import os
import requests

from itertools import chain

from .models import ChannelPointReward, CommandFunction
from .serializers import ChannelPointRewardSerializer
from accounts.models import TwitchUser, SpotifyCredentials
from bot.models import *

from datetime import datetime
from django.contrib import messages
from accounts.models import TwitchUser
from django.core.validators import RegexValidator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.http import QueryDict
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response as RESTResponse

from typing import Union
from utils import misc, users, views
from utils.twitch import api as TwitchAPI


REWARD_CODES = ["songreq", "songskip", "chatgpt", "gptimage", "soundreq", "ytreq"]
REWARD_TITLES = {
    "songreq": "Spotify Song Requests",
    "songskip": "Spotify Song Skips", 
    "chatgpt": "ChatGPT Chat Requests",
    "gptimage": "ChatGPT Image Requests",
    "soundreq": "Sound Requests",
    "ytreq": "YouTube Requests",
}


# ======================================================================================================================
# VIEWS
# ======================================================================================================================
@never_cache
@views.twitchRequired
def index(request: HttpRequest):
    user = request.user

    # Get the user's custom rewards
    rewards_from_api = users.getTwitchRewards(user.twitch_id)
    if rewards_from_api:
        syncRewards(user, rewards_from_api)

    ctx = views.buildBaseContext(user)

    ctx.update({
        'active_session': user.active_session,
        'overlay_link': "{}{}{}".format(os.getenv("HOST_URL"), "/overlay/", user.username)
    })
    user.refresh_from_db()

    try:
        spotify_authenticated = user.spotifycredentials.code is not None
        spotify_current = set(os.getenv('SPOTIFY_SCOPE').split(' ')).issubset(set(user.spotifycredentials.scope))
    except SpotifyCredentials.DoesNotExist:
        spotify_authenticated = False
        spotify_current = False
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

    return render(request, "functions/index.html", context=ctx)


@never_cache
@views.twitchRequired
def configure(request: HttpRequest):
    user = request.user
    songreq_vars = SongReqVars.objects.filter(user=user).first()
    songskip_vars = SongSkipVars.objects.filter(user=user).first()
    chatgpt_vars = ChatGPTVars.objects.filter(user=user).first()
    gptimage_vars = GPTImageVars.objects.filter(user=user).first()
    ytreq_vars = YTReqVars.objects.filter(user=user).first()

    ctx = views.buildBaseContext(user)

    ctx.update({
        'songreq': songreq_vars,
        'songskip': songskip_vars,
        'chatgpt': chatgpt_vars,
        'gptimage': gptimage_vars,
        'ytreq': ytreq_vars
    })

    return render(request, "functions/configurator.html", context=ctx)


# ======================================================================================================================
# API VIEWS
# ======================================================================================================================
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def reward(request, format=None):
    """
    Creates a channel point reward on behalf of the user.
    """
    if request.method == "PUT":
        result = createReward(request.user, request.data)
        if not result['ok']:
            return RESTResponse(result, status=(result['code'] or status.HTTP_400_BAD_REQUEST))
        return RESTResponse(status=status.HTTP_200_OK)
    

@api_view(["GET", "PUT", "DELETE", "PATCH"])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def binds(request, format=None):
    """
    Retrieve the list of reward and command function binds the user has, create, delete, or update them.
    """
    if request.method == "GET":
        # Get the list of function binds the user has.
        template = request.query_params.get("template", None)
        method = request.query_params.get("method", "command")
        if template is None:
            return RESTResponse({'msg': "Template was not supplied a value."}, status=status.HTTP_400_BAD_REQUEST)
        known_rewards = ChannelPointReward.objects.filter(user=request.user)
        ctx = {
            'is_affiliate': request.user.is_affiliate,
            'func_code_lookup': REWARD_TITLES,
            'twitch_rewards': known_rewards,
            'binds': fetchBinds(request.user),
        }
        if template != "setter":
            return RESTResponse(data=ctx, template_name="functions/viewer.html")
        
        if method == "reward" and request.user.is_affiliate:
            return RESTResponse(data=ctx, template_name="functions/reward_setter.html")
        else:
            return RESTResponse(data=ctx, template_name="functions/command_setter.html")
        
    
    if request.method == "PUT":
        # Create a function bind.
        method = request.data.get("method", None)
        function = request.data.get("function", None)
        if None in [method, function]:
            return RESTResponse({'msg': "Failed to create function. \{method, function\} has a null value."}, status=status.HTTP_400_BAD_REQUEST)
        if function not in REWARD_CODES:
            return RESTResponse({'msg': "Failed to create function. \{function\} is an invalid value."}, status=status.HTTP_400_BAD_REQUEST)
        if method == "reward":
            reward_id = request.data.get("id", None)
            if reward_id is None:
                return RESTResponse({'msg': "Failed to create reward function. \{reward_id\} has a null value."}, status=status.HTTP_400_BAD_REQUEST)
            chosen_reward = ChannelPointReward.objects.filter(reward_id=reward_id).first()
            chosen_reward.binded_to = [function]
            chosen_reward.save()
            return RESTResponse(status=status.HTTP_200_OK)
        if method == "command":
            command_name = request.data.get("commandName", None)
            has_cooldown = request.data.get("hasCooldown", None)
            global_cooldown = request.data.get("globalCooldown", None)
            user_cooldown = request.data.get("userCooldown", None)
            if None in [command_name, has_cooldown, global_cooldown, user_cooldown]:
                return RESTResponse({'msg': "Failed to create command function. \{command_name, has_cooldown, global_cooldown, user_cooldown\} has a null value."}, status=status.HTTP_400_BAD_REQUEST)
            command_func_params = {
                'user': request.user,
                'name': command_name,
                'binded_to': [function],
                'has_cooldown': misc.strToBool(has_cooldown)
            }
            if misc.strToBool(has_cooldown):
                command_func_params.update({
                    'global_cooldown': max(1, int(global_cooldown)),
                    'user_cooldown': max(1, int(user_cooldown))
                })
            created_command = CommandFunction(**command_func_params)
            created_command.save()
            return RESTResponse(status=status.HTTP_200_OK)
    
    if request.method == "DELETE":
        # Delete a function bind.
        function = request.data.get("function", None)
        method = request.data.get("method", None)
        if None in [function, method]:
            return RESTResponse({'msg': "Failed to unbind channel point function; \{function, method\} has a null value."}, status=status.HTTP_400_BAD_REQUEST)
        if function not in REWARD_CODES:
            return RESTResponse({'msg': "Failed to delete function. \{function\} is an invalid value."}, status=status.HTTP_400_BAD_REQUEST)
        if method == "reward":
            current_binded_reward = ChannelPointReward.objects.filter(user=request.user, binded_to__contains=[function]).first()
            if not current_binded_reward.bot_created:
                # Bot didn't create this reward. Just unbind and return
                current_binded_reward.binded_to.remove(function)
                current_binded_reward.save()
                return RESTResponse(status=status.HTTP_204_NO_CONTENT)
            # Bot created this reward; delete the channel point reward from Twitch, and from our DB
            response = TwitchAPI.deleteCustomReward(request.user.twitch_id, request.user.twitchcredentials.access_token, current_binded_reward.reward_id)
            if not response['ok']:
                return RESTResponse(response, status=(response['code'] or status.HTTP_400_BAD_REQUEST))
            current_binded_reward.delete()
        if method == "command":
            current_binded_command = CommandFunction.objects.filter(user=request.user, binded_to__contains=[function]).first()
            current_binded_command.delete()
        return RESTResponse(status=status.HTTP_204_NO_CONTENT)
    
    if request.method == "PATCH":
        # Change a function's bind, or the function itself.
        old_function = request.data.get("oldFunction", None)
        old_reward_id = request.data.get("oldID", None)
        new_function = request.data.get("newFunction", None)
        new_reward_id = request.data.get("newID", None)
        if None in [old_function, old_reward_id, new_function, new_reward_id]:
            return RESTResponse({'msg': "Failed to update channel point function; one or more variables are null."}, status=status.HTTP_400_BAD_REQUEST)
        if old_function not in REWARD_CODES or new_function not in REWARD_CODES:
            return RESTResponse({'msg': "Failed to create function. \{old_function, new_function\} has an invalid value."}, status=status.HTTP_400_BAD_REQUEST)
        known_rewards = ChannelPointReward.objects.filter(user=request.user)
        current_binded_reward = known_rewards.filter(binded_to__contains=[old_function]).first()
        # Replaced function bind
        if old_reward_id != new_reward_id:
            current_binded_reward.binded_to.remove(old_function)
            current_binded_reward.save()
            new_binded_reward = known_rewards.filter(reward_id=new_reward_id).first()
            new_binded_reward.binded_to = [old_function]
            new_binded_reward.save()
            current_binded_reward = new_binded_reward
        # Replaced function
        if old_function != new_function:
            current_binded_reward.binded_to = [new_function]
            current_binded_reward.save()
        return RESTResponse(status=status.HTTP_200_OK)
    

@api_view(["PATCH"])
def vars(request, format=None):
    function = request.data.get("function", None)

    if function == "songreq":
        emote = request.data.get("emote", None)
        if emote is None:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        new_vars = SongReqVars(
            user = request.user,
            emote = misc.trimStr(emote, 256)
        )

    if function == "songskip":
        emote = request.data.get("emote", None)
        if emote is None:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        new_vars = SongSkipVars(
            user = request.user,
            emote = misc.trimStr(emote, 256)
        )

    if function == "chatgpt":
        clearsize = request.data.get("clearsize", None)
        showfull = request.data.get("showfull", None)
        maxprompttokens = request.data.get("maxprompttokens", None)
        if None in [clearsize, showfull, maxprompttokens]:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        new_vars = ChatGPTVars(
            user = request.user,
            clearsize = misc.clampInt(int(clearsize), 1, 20),
            showfull = misc.strToBool(showfull),
            maxprompttokens = max(int(maxprompttokens), 1)
        )

    if function == "ytreq":
        maxsecs = request.data.get("maxsecs", None)
        mutespotify = request.data.get("mutespotify", None)
        if None in [maxsecs, mutespotify]:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        new_vars = YTReqVars(
            user = request.user,
            maxsecs = max(int(maxsecs), 1),
            mutespotify = misc.strToBool(mutespotify),
        )
        
    new_vars.save()
    return RESTResponse(status=status.HTTP_200_OK)


# ======================================================================================================================
# FUNCTIONS
# ======================================================================================================================
def createReward(user: TwitchUser, data: QueryDict) -> dict:
    known_rewards = ChannelPointReward.objects.filter(user=user)
    reward_name = data.get("rewardName", None)
    description = data.get("rewardDescription", None)
    text_required = data.get("rewardText", None) # Bool
    cost = data.get("rewardCost", None)
    color = data.get("rewardColor", None)
    # TODO-MEDIUM -- skipped rewards can't be refunded. Make this instead auto-accept and auto-refund? and not auto-accept always?
    # auto_skip = post_data.get("auto_skip", None)
    auto_skip = False # Bool
    has_cooldown = data.get("rewardCooldown", None) # Bool
    cooldown_time = data.get("rewardCDTime", None)
    limit_per_stream = data.get("rewardCDLimit", None)
    user_limit_per_stream = data.get("rewardCDLimituser", None)
    function = data.get("function", None)

    all_vars = [reward_name, description, text_required, cost, color, auto_skip, has_cooldown, cooldown_time, limit_per_stream, user_limit_per_stream, function]
    if None in all_vars:
        return {'ok': False, 'msg': "One or more required fields were empty."}

    reward_data = {
        'title': misc.trimStr(reward_name, 45),
        'cost': max(1, int(cost)),
        'prompt': misc.trimStr(description, 200),
        'is_enabled': True,
        'background_color': color, # TODO: is this always valid?
        'is_user_input_required': misc.strToBool(text_required),
        'should_redemptions_skip_request_queue': False
    }

    if misc.strToBool(has_cooldown):
        reward_data.update({
            'is_max_per_stream_enabled': int(limit_per_stream) > 0,
            'max_per_stream': max(1, int(limit_per_stream)),
            'is_max_per_user_per_stream_enabled': int(user_limit_per_stream) > 0,
            'max_per_user_per_stream': max(1, int(user_limit_per_stream)),
            'is_global_cooldown_enabled': int(cooldown_time) > 0,
            'global_cooldown_seconds': max(60, int(cooldown_time)),
            'should_redemptions_skip_request_queue': auto_skip
        })

    response = TwitchAPI.addCustomReward(user.twitch_id, user.twitchcredentials.access_token, reward_data)
    if not response['ok']:
        return response
    else:
        response_reward_data = {
            'id': response['data'][0]['id'],
            'title': response['data'][0]['title'],
            'color': response['data'][0]['background_color'],
            'image': response['data'][0]['image'] if response['data'][0]['image'] is not None else response['data'][0]['default_image']
        }

    # Unbind any function bind currently in the DB
    old_bind = known_rewards.filter(binded_to__contains=[function]).first()
    if old_bind is not None:
        old_bind.binded_to.remove(function)
        old_bind.save()

    # And write the new one in
    new_reward = ChannelPointReward(
        reward_id = response_reward_data['id'],
        reward_title = response_reward_data['title'],
        color = response_reward_data['color'],
        image = response_reward_data['image'],
        user = user,
        bot_created = True,
        binded_to = [function]
    )
    new_reward.save()
    return {
        'ok': True,
        'reward_data': response_reward_data,
        'reward': new_reward
    }


def syncRewards(user: TwitchUser, incoming_rewards: list) -> int:
    """
    Takes a list of incoming channel point rewards from Twitch's API and makes sure the DB is synced.
    Returns 1 if successful.
    """
    # Check if user has rewards to begin with.
    if len(incoming_rewards) == 0:
        # User doesn't have any channel point rewards.
        # 0: Didn't sync anything at all. Nothing to build.
        return 0

    incoming_rewards_by_id = parseRewardsByID(incoming_rewards)
    known_rewards = ChannelPointReward.objects.filter(user=user)

    # Any reward IDs that we know of that aren't incoming?
    # That means that we know of a reward that was deleted in between their last visit and now.
    known_reward_ids = [reward.reward_id for reward in known_rewards]   # What if known_rewards is empty?
    for known_reward_id in known_reward_ids:
        if known_reward_id not in incoming_rewards_by_id:
            known_rewards.get(reward_id=known_reward_id).delete()

    # Any incoming reward IDs that we don't know of?
    # This is if a reward was created in between their last visit and now.
    for incoming_reward_id, incoming_reward_data in incoming_rewards_by_id.items():
        if incoming_reward_id not in known_reward_ids:
            # Add the incoming reward data to DB
            incoming_reward = ChannelPointReward(
                reward_id = incoming_reward_data['id'],     # incoming_reward_id
                reward_title = incoming_reward_data['title'],
                color = incoming_reward_data['background_color'],
                image = incoming_reward_data['image']['url_1x'] if incoming_reward_data['image'] is not None else incoming_reward_data['default_image']['url_1x'],
                user = user
            )
            incoming_reward.save()

    # 1: Successfully hit DB to delete old rewards/update new ones.
    return 1


def fetchBinds(user: TwitchUser) -> dict:
    """
    Takes a list of all binded rewards/commands, and puts it in a dict format for templates.

    binds: {
        rewards: {
            songreq: {
                ...
            }
        },
        commands: {
            songreq: {
                ...
            }
        }
    }
    """
    return {
        'rewards': fetchRewardBinds(user),
        'commands': fetchCommandBinds(user)
    }


def fetchRewardBinds(user: TwitchUser) -> dict:
    binds = {}
    binded_rewards = ChannelPointReward.objects.filter(user=user, binded_to__len__gt=0)
    for code in REWARD_CODES:
        if code == "gptimage" and user.username != "xzmozxx":
            continue
        # TODO: why does `[code]` work and not `code` ???
        # https://docs.djangoproject.com/en/4.2/ref/models/querysets/#contains
        binded_reward = binded_rewards.filter(binded_to__contains=[code]).first()
        if binded_reward:
            binds.update({
                code: {
                    'id': binded_reward.reward_id,
                    'title': binded_reward.reward_title,
                    'color': binded_reward.color,
                    'image': binded_reward.image,
                    'func_code_title': REWARD_TITLES[code]
                }
            })
    return binds


def fetchCommandBinds(user: TwitchUser) -> dict:
    binds = {}
    binded_commands = CommandFunction.objects.filter(user=user, binded_to__len__gt=0)
    for code in REWARD_CODES:
        if code == "gptimage" and user.username != "xzmozxx":
            continue
        # TODO: why does `[code]` work and not `code` ???
        # https://docs.djangoproject.com/en/4.2/ref/models/querysets/#contains
        binded_command = binded_commands.filter(binded_to__contains=[code]).first()
        if binded_command:
            binds.update({
                code: {
                    'id': binded_command.id,
                    'name': binded_command.name,
                    'has_cooldown': binded_command.has_cooldown,
                    'global_cooldown': binded_command.global_cooldown,
                    'user_cooldown': binded_command.user_cooldown,
                    'func_code_title': REWARD_TITLES[code]
                }
            })
    return binds


def parseRewardsByID(rewards_data) -> dict:
    return {reward['id']: reward for reward in rewards_data}