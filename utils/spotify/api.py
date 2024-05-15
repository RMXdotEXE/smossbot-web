import base64
import json
import os
import requests


def getToken(code:str) -> dict:
    """
    Takes an authorization code, and asks Spotify to get an OAuth token from it.
    Returns a dict indicating the result, including the credentials received. 
    """
    result = {
        'ok': False,
        'msg': "The authorization code provided to Spotify was invalid.",
        'credentials': {}
    }

    auth_str = "{}:{}".format(os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET'))
    encoded_str = base64.urlsafe_b64encode(auth_str.encode()).decode()

    header = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Authorization': "Basic {}".format(encoded_str)
    }
    params = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI')
    }

    # https://developer.spotify.com/documentation/web-api/tutorials/code-flow
    resp = requests.post("https://accounts.spotify.com/api/token", params=params, headers=header)
    if resp.ok:
        result['ok'] = True
        result['msg'] = "Authorization successful; token granted!"
        result['credentials'] = json.loads(resp.content.decode())

    return result