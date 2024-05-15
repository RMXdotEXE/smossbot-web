import os

from .twitch import api as TwitchAPI
from accounts.models import TwitchUser, TwitchCredentials


def validateUser(user:TwitchUser) -> dict:
    """
    Validates the user's credentials with Twitch.
    Returns a dict indicating results.
    """
    return validate(user=user, access_token=None)


def validateToken(access_token:str) -> dict:
    """
    Validates the given access token.
    Returns a dict indicating results.
    """
    return validate(user=None, access_token=access_token)


def validate(user: TwitchUser = None, access_token: str = None) -> dict:
    """
    Tests to see if the user's Twitch OAuth token is still valid, including its scopes.
    The difference between this and .twitch.api.validateToken() is that this also tests/validates for scopes,
    regarding this site. The latter only goes to Twitch for validation; this function should be used.
    Returns a dict indicating the result, including information associated with the token.
    """
    # Validate their token to make sure we're still dealing with a valid access token.
    # Twitch requires this to be done hourly, but I'm just gonna do it every time. Not terribly efficient.
    # TODO: Find potential ways to make this better.
    valid = False
    required_scopes = os.getenv('TWITCH_SCOPE').split(' ')

    try:
        result = TwitchAPI.validateToken(access_token if access_token else user.twitchcredentials.access_token)
    except:
        return {'ok': False, 'msg': "Fatal error occured passing the token for validation to Twitch.", 'credentials': {}}
    
    if result['ok']:
        # Token validated!
        # Let's also make sure they have the right scopes
        valid = set(result['credentials']['scopes']) == set(required_scopes)
    elif user:
        # Token not validated, but we have a user tied to this
        # Attempt a re-auth
        result = twitchReauth(user)
        valid = result['ok'] and (set(result['credentials']['scope']) == set(required_scopes))
    result['ok'] = valid
    return result


def twitchReauth(user: TwitchUser) -> dict:
    """
    Takes a user, and asks the API to reauth them. The new credentials are saved into the DB,
    and returned. {'ok': False, 'msg': "..."} is returned if the auth was unsuccessful.
    """
    reauth = TwitchAPI.reauthToken(user.twitchcredentials.refresh_token)
    reauth_credentials = reauth['credentials']
    if not reauth_credentials:
        return reauth

    user.twitchcredentials.access_token = reauth_credentials['access_token']
    user.twitchcredentials.expires_in = reauth_credentials['expires_in']
    user.twitchcredentials.refresh_token = reauth_credentials['refresh_token']
    user.twitchcredentials.token_type = reauth_credentials['token_type']
    user.twitchcredentials.scope = reauth_credentials['scope']
    user.twitchcredentials.save()

    return reauth


def buildTwitchAuthURL() -> str:
    """
    Returns a URL that is presented to a user for smossbot to gain authorization.
    A valid OAuth token, and credentials, will be given.
    """
    url = "https://id.twitch.tv/oauth2/authorize?" + \
        "client_id=" + os.getenv('TWITCH_CLIENT_ID') + \
        "&redirect_uri=" + os.getenv('TWITCH_REDIRECT_URI') + \
        "&response_type=code" + \
        "&scope=" + os.getenv('TWITCH_SCOPE')
    return url