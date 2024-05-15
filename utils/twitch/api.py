import json
import os
import requests

from accounts.models import TwitchUser


def getToken(code:str) -> dict:
    """
    Takes an authorization code, and asks Twitch to get an OAuth token from it.
    Returns a dict indicating the result, including the credentials received. 
    """
    result = {
        'ok': False,
        'msg': "The authorization code provided to Twitch was invalid.",
        'credentials': {}
    }

    # Automatically encodes to x-www-form-urlencoded
    body = {
        'client_id': os.getenv('TWITCH_CLIENT_ID'),
        'client_secret': os.getenv('TWITCH_CLIENT_SECRET'),
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': os.getenv('TWITCH_REDIRECT_URI')
    }
    # https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#use-the-authorization-code-to-get-a-token
    resp = requests.post("https://id.twitch.tv/oauth2/token", data=body)
    if resp.ok:
        result['ok'] = True
        result['msg'] = "Authorization successful; token granted!"
        result['credentials'] = json.loads(resp.content.decode())
        
    return result


def validateToken(auth_token:str) -> dict:
    """
    Tests to see if the provided Twitch OAuth token is valid according to Twitch.
    Returns a dict indicating the result, including information associated with the token.
    """
    result = {
        'ok': False,
        'msg': "Twitch has determined the token to be invalid. This needs to be refreshed.",
        'credentials': {}
    }

    header = {'Authorization': "OAuth {}".format(auth_token)}
    # https://dev.twitch.tv/docs/authentication/validate-tokens/
    resp = requests.get("https://id.twitch.tv/oauth2/validate", headers=header)
    if resp.ok:
        resp_data = json.loads(resp.content.decode())
        result['ok'] = True
        result['msg'] = "Token validation from Twitch successful."
        result['credentials'] = {
            'login': resp_data['login'],
            'id': resp_data['user_id'],
            'scopes': resp_data['scopes']
        }
    return result


def reauthToken(refresh_token:str) -> dict:
    """
    Takes a refresh token, and gets new Twitch credentials for the owner of refresh_token.
    Returns a dict with the new, fresh credentials.
    """
    result = {
        'ok': False,
        'msg': "Twitch re-authentication was not successful.",
        'credentials': {}
    }

    header = {
        'Content-Type': "application/x-www-form-urlencoded"
    }
    params = {
        'client_id': os.getenv('TWITCH_CLIENT_ID'),
        'client_secret': os.getenv('TWITCH_CLIENT_SECRET'),
        'grant_type': "refresh_token",
        'refresh_token': refresh_token
    }
    resp = requests.post("https://id.twitch.tv/oauth2/token", headers=header, params=params)
    if not resp.ok:
        return result

    data = json.loads(resp.content.decode())
    result['credentials']['access_token'] = data['access_token']
    result['credentials']['expires_in'] = data['expires_in']
    result['credentials']['refresh_token'] = data['refresh_token']
    result['credentials']['token_type'] = data['token_type']
    result['credentials']['scope'] = data['scope']

    result['ok'] = True
    result['msg'] = "Twitch re-authentication was successful!"
    return result


def getUser(twitch_id: int, token: str = None) -> dict:
    """
    Takes a twitch_id and gets the user's information associated with that ID.
    Returns a dict indicating results, including the user's information.
    """
    result = {
        'ok': False,
        'msg': "Error occured retrieving information; user doesn't exist with that ID.",
        'data': {}
    }
    user = TwitchUser.objects.filter(pk=twitch_id).first()
    if user is None:
        return result

    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(token if token else user.twitchcredentials.access_token)
    }

    # https://dev.twitch.tv/docs/api/reference/#get-users
    resp = requests.get("https://api.twitch.tv/helix/users", headers=header)
    if not resp.ok:
        result['msg'] = "Error occured retrieving information; try refreshing."
        return result
    else:
        result['ok'] = True
        result['msg'] = "Successfully retrieved information!"
        result['data'] = json.loads(resp.content.decode())

    return result



def getCustomRewards(twitch_id: int, twitch_auth_token: str) -> dict:
    """
    Takes a twitch_id and auth_token, and gets the custom rewards that are associated with that user.
    Returns the channel point rewards as a list of dictionaries.
    """
    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(twitch_auth_token)
    }
    # https://dev.twitch.tv/docs/api/reference/#get-custom-reward
    resp = requests.get("https://api.twitch.tv/helix/channel_points/custom_rewards", params={'broadcaster_id': twitch_id}, headers=header)

    if resp.ok:
        data = json.loads(resp.content.decode())
        return {
            'ok': True,
            'code': resp.status_code, 
            'data': data['data'], 
            'msg': "Success."
        }
    
    error_msg = ""
    if   resp.status_code == 400: error_msg = "No Twitch ID was specified in the request; please refresh or report the problem if it persists. Thank you!"
    elif resp.status_code == 401: error_msg = "The authorization provided was invalid; please relog and try again, and report if it persists. Thank you!"
    elif resp.status_code == 403: error_msg = "Channel point rewards aren't unlocked for you yet because you're not a Partner or Affiliate; apologies!"
    elif resp.status_code == 404: error_msg = "No custom rewards were found with the IDs we asked for; you shouldn't ever get this error, so let me know if you see this!"
    elif resp.status_code == 500: error_msg = "Twitch had an internal server error; try again in a moment."
    else: error_msg = "An error occured getting the custom rewards."

    return {
        'ok': False,
        'code': resp.status_code,
        'msg': error_msg
    }


def addCustomReward(twitch_id: int, twitch_auth_token: str, reward_data: dict) -> dict:
    """
    Takes a twitch_id and auth_token, and adds a custom channel point reward.
    Returns the channel point rewards as a list of dictionaries.
    """
    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(twitch_auth_token)
    }

    # https://dev.twitch.tv/docs/api/reference/#create-custom-rewards
    resp = requests.post("https://api.twitch.tv/helix/channel_points/custom_rewards", headers=header, json=reward_data, params={'broadcaster_id': twitch_id})

    if resp.ok:
        data = json.loads(resp.content.decode())
        return {
            'ok': True,
            'code': resp.status_code,
            'data': data['data'],
            'msg': "Success."
        }
    
    error_msg = ""
    if   resp.status_code == 400: error_msg = ("No Twitch ID was specified in the request, the name for the channel point reward matches an existing one, "
            "or one of the parameters was invalid. Try again, refresh, or report the problem if it persists. Thank you!")
    elif resp.status_code == 401: error_msg = "The authorization provided was invalid; please relog and try again, and report if it persists. Thank you!"
    elif resp.status_code == 403: error_msg = "Channel point rewards aren't unlocked for you yet because you're not a Partner or Affiliate; apologies!"
    elif resp.status_code == 500: error_msg = "Twitch had an internal server error; try again in a moment."
    else: error_msg = "An error occured getting the custom rewards."

    return {
        'ok': False,
        'code': resp.status_code,
        'msg': error_msg
    }


def deleteCustomReward(twitch_id: int, twitch_auth_token: str, reward_id: str) -> dict:
    """
    Takes a twitch_id and auth_token, and deletes a custom channel point reward.
    Returns whether the operation was a success or not.
    """
    header = {
        'Client-ID': os.getenv('TWITCH_CLIENT_ID'),
        'Authorization': "Bearer {}".format(twitch_auth_token)
    }

    # https://dev.twitch.tv/docs/api/reference/#delete-custom-reward
    resp = requests.delete("https://api.twitch.tv/helix/channel_points/custom_rewards", headers=header, params={'broadcaster_id': twitch_id, 'id': reward_id})

    if resp.ok:
        return {
            'ok': True,
            'code': resp.status_code,
            'data': None,
            'msg': "Success."
        }
    
    error_msg = ""
    if   resp.status_code == 400: error_msg = "No Twitch ID or reward_id was specified in the request. Try again, refresh, or report the problem if it persists. Thank you!"
    elif resp.status_code == 401: error_msg = "The authorization provided was invalid; please relog and try again, and report if it persists. Thank you!"
    elif resp.status_code == 403: error_msg = ("smossbot tried to delete the reward but it wasn't the one that created it. If you're certain you created the reward here, "
            "please report this! This is super unusual behaviour. (This error could also mean you aren't a Twitch partner/affiliate, but this isn't it.)")
    elif resp.status_code == 404: error_msg = "The reward attempting deletion doesn't exist anymore. Double-check it still exists, and let me know if this issue persists."
    elif resp.status_code == 500: error_msg = "Twitch had an internal server error; try again in a moment."
    else: error_msg = "An error occured deleting the custom reward."

    return {
        'ok': False,
        'code': resp.status_code,
        'msg': error_msg
    }