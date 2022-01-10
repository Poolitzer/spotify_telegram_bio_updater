# spotify_telegram_bio_updater
This userbot updates the biography of a telegram user according to their current spotify playback. If no playback is active, the bot changes the bio back to the original one from the user.

## Setup

This script will do an interactive setup the first time you run bot.py. If you want to do it by yourself, you can follow the steps below, but that isn't necessary anymore.

Just remember to run `pip install -r requirements.txt`.

Depreciated manual steps:

0. Ensure you have python 3.6+ installed and then run `pip install -r requirements.txt`.
1. Get your spotify client_id and your client_secret from https://developer.spotify.com/dashboard/. If you need more help, have a look [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app). Set a Rediret URI to http://localhost:1234/callback
2. Get your telegram app api_id and api_hash from https://my.telegram.org/. If you need more help, have a look [here](https://telethon.readthedocs.io/en/latest/extra/basic/creating-a-client.html#creating-a-client).
3. If you want to have a log channel or group or so, paste its invite link or id in the LOG variable. If you leave it at "me", you will see those in your saved chat. Only if errors occur ofc ;)
4. Paste all these values in their respective variables at [constants.py](/constants.py). While you are at it, you can also paste an initial biography there. Just take your current one. This is highly recommended. If you don't do this **and** have a currently playing track, the bot has at its first start no idea what your original biography is. Just do it, please.
5. You are going to generate a token here which is only valid for a short amount of time, so be sure to run generate.py quickly after this. Open the following link (change CLIENT_ID to you client_id): https://accounts.spotify.com/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=http://localhost:1234/callback&scope=user-read-playback-state%20user-read-currently-playing
6. After you grant permission, you get redirected to https://example.com/callback?code=_. Copy everything after the code, this is you initial token.
7. Now you can run [generate.py](/generate.py). This will generate a json file named database.
8. You are almost done. If you now run [bot.py](/bot.py), all you need to do is log into your telegram account. Follow the instructions on screen.
9. Now you are really done.

## Important Information

You can shut the bot down if you want/need to. Write `//stop` anywhere you want. If you want to change the command, edit SHUTDOWN_COMMAND in the [constants](/constants.py).

## Warning

This bot uses the emoji 🎶 to determine if the current bio is an active spotify biography or not. This means you mustn't use this emoji on your original biographies or the bot will probably break. Don't do it, thanks.

## But I want to

Great news. Just change the KEY variable in [constants](/constants.py) file. Don't ever use your new KEY in your biographies though!

## Issues? Need help? Want to tell me something?

Well, just create an issue here. You can also ping me on [telegram](https://t.me/poolitzer).
