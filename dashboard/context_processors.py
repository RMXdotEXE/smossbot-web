from accounts.models import TwitchUser

def username(request):
    try:
        user = request.user
        username = user.username
    except TwitchUser.DoesNotExist:
        username = None

    return {'username': username}
