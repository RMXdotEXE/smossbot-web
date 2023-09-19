from dashboard.models import TwitchUser

def username(request):
    try:
        user = TwitchUser.objects.get(twitch_id=request.session.get('twitch_id', None))
        username = user.username
    except TwitchUser.DoesNotExist:
        username = None

    return {'username': username}
