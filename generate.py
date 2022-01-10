import json
from constants import CLIENT_SECRET, CLIENT_ID, INITIAL_BIO, INITIAL_TOKEN

from aiohttp import ClientSession

body = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "grant_type": "authorization_code",
    "redirect_uri": "http://localhost:1234/callback",
    "code": INITIAL_TOKEN,
}

async with ClientSession() as session:
    async with session.post(
        "https://accounts.spotify.com/api/token", data=body
    ) as post_response:
        save = await post_response.json()
        to_create = {
            "bio": INITIAL_BIO,
            "access_token": save["access_token"],
            "refresh_token": save["refresh_token"],
            "telegram_spam": False,
            "spotify_spam": False,
        }
        with open("./database.json", "w") as outfile:
            json.dump(to_create, outfile, indent=4, sort_keys=True)
