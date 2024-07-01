import os

from .models import *
from accounts.models import TwitchUser
from django.http import HttpRequest
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response as RESTResponse
from utils import misc, views


def process_req(request, user_hash):
    # TODO-MED: make user_hash an actual hash
    url = None
    if os.getenv('DEBUG') == "True":
        url = "ws://localhost:5000/ws"
    else:
        url = "wss://www.smossbot.com:5000/ws"

    user = TwitchUser.objects.filter(username=user_hash).first()

    ctx = {
        'username': user_hash,
        'url': url,
        'songreqoverlay': user.songreqoverlay,
        'ytreqoverlay': user.ytreqoverlay
    }
        
    return render(request, "overlay/overlay.html", context=ctx)


def configure(request: HttpRequest):
    ctx = views.buildBaseContext(request.user)
    ctx.update({
        'songreqoverlay': request.user.songreqoverlay,
        'ytreqoverlay': request.user.ytreqoverlay,
        'overlay_link': "{}{}{}".format(os.getenv("HOST_URL"), "/overlay/user/", request.user.username)
    })

    return render(request, "overlay/configurator.html", context=ctx)


@api_view(["PATCH"])
@renderer_classes([JSONRenderer])
def configurations(request, format=None):
    overlay_function = request.data.get("overlay_function", None)

    if not overlay_function:
        return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
    
    new_vars = None
    
    if overlay_function == "songreq":
        enabled = request.data.get("enabled", None)
        # constant = request.data.get("constant", None)
        background = request.data.get("background", None)
        vertical_anchor_pos = request.data.get("verticalAnchorPos", None)
        horizontal_anchor_pos = request.data.get("horizontalAnchorPos", None)
        if None in [enabled, background, vertical_anchor_pos, horizontal_anchor_pos]:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        new_vars = SongReqOverlay(
            user = request.user,
            enabled = misc.strToBool(enabled),
            # constant = misc.strToBool(constant),
            background = misc.strToBool(background),
            vertical_anchor_pos = vertical_anchor_pos.lower(),
            horizontal_anchor_pos = horizontal_anchor_pos.lower(),
        )
    elif overlay_function == "ytreq":
        width = request.data.get("width", None)
        height = request.data.get("height", None)
        vertical_anchor_pos = request.data.get("verticalAnchorPos", None)
        horizontal_anchor_pos = request.data.get("horizontalAnchorPos", None)
        if None in [width, height, vertical_anchor_pos, horizontal_anchor_pos]:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        new_vars = YTReqOverlay(
            user = request.user,
            width = misc.clampInt(int(width), 0, 2147483647),
            height = misc.clampInt(int(height), 0, 2147483647),
            vertical_anchor_pos = vertical_anchor_pos.lower(),
            horizontal_anchor_pos = horizontal_anchor_pos.lower(),
        )
    else:
        return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
    
    new_vars.save()
    return RESTResponse(status=status.HTTP_200_OK)