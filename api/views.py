import json
import os
import requests

from accounts.models import TwitchUser
from files.models import UploadedFile
from django.http import HttpRequest, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response as RESTResponse
from utils import misc


# ======================================================================================================================
# API VIEWS
# ======================================================================================================================
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([JSONRenderer, TemplateHTMLRenderer])
def session(request, format=None):
    """
    Gets/controls the user's session. If a session is active, that means the bot is active
    and is listening in their chat. If it's inactive, the bot doesn't listen.
    """
    if request.method == "GET":
        return RESTResponse(data={'active_session': request.user.active_session}, template_name="dashboard/session_controller.html")

    if request.method == "POST":
        _session = request.data.get("session", None)
        if _session is None:
            return RESTResponse(status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        post_url = "{}session".format(os.getenv('BACKEND_API'))
        data = {
            'user': request.user.username,
            'id': user.twitch_id,
            'session': misc.strToBool(_session)
        }
        resp = requests.post(post_url, json=data)
        if not resp.ok:
            return RESTResponse(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return RESTResponse(status=status.HTTP_200_OK)


def taggedfile(request):
    user_hash = request.GET.get("user_hash", None)
    tag = request.GET.get("tag", None)

    response = {
        'exists': False,
        'filename': None,
        'errormsg': "An error occured sending the request to the server."
    }

    if not user_hash or not tag:
        return JsonResponse(response)
    
    user = TwitchUser.objects.filter(username=user_hash).first()
    if not user:
        response['errormsg'] = "The username was unable to be found."
        return JsonResponse(response)
    
    matching_file = UploadedFile.objects.filter(user=user, tag=tag).first()
    if not matching_file:
        response['errormsg'] = "No file exists with the specified tag."
        return JsonResponse(response)

    response['exists'] = True
    response['filename'] = matching_file.file.name

    return JsonResponse(response)