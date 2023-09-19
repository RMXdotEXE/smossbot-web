from dashboard.models import TwitchUser, UploadedFile
from django.http import JsonResponse


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
    response['errormsg'] = "The username was unable to be found."


    user = TwitchUser.objects.filter(username=user_hash).first()
    if not user:
        return JsonResponse(response)
    response['errormsg'] = "No file exists with the specified tag."

    matching_file = UploadedFile.objects.filter(user=user, tag=tag).first()
    if not matching_file:
        return JsonResponse(response)

    response['exists'] = True
    response['filename'] = matching_file.file.name

    return JsonResponse(response)
