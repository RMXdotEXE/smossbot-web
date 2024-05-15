from .models import TwitchUser
from django.contrib.auth.backends import BaseBackend
from utils.auth import validateToken, twitchReauth
from utils.twitch import api as TwitchAPI


class TwitchAuthBackend(BaseBackend):
    def authenticate(self, request, token=None):
        if token is None: return
        token_data = validateToken(token)
        if token_data['ok']:
            credentials = token_data['credentials']
            try:
                # Returning user. All good!
                user = TwitchUser.objects.get(username=credentials['login'])
            except TwitchUser.DoesNotExist:
                # First-time sign-in; do onboard.
                user = TwitchUser(
                    twitch_id = credentials['id'],
                    username = credentials['login']
                )
                user.save()
                pass
            # Update affiliate status
            info_result = TwitchAPI.getUser(user.twitch_id, token)
            if not info_result['ok']:
                twitchReauth(user)
                info_result = TwitchAPI.getUser(user.twitch_id)
                if not info_result['ok']:
                    return None
                
            user.is_affiliate = info_result['data']['data'][0]['broadcaster_type'] != ""
            user.save()
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return TwitchUser.objects.get(pk=user_id)
        except TwitchUser.DoesNotExist:
            return None