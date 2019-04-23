# spotify_telegram_bio_updater
This userbot updates the biography of a telegram user according to their current spotify playback. If no playback is active, the bot changes the bio back to the original one from the user.

## Setup

If you follow this steps, you can use this project easily for yourself.

0. Ensure you have python 3.6+ installed and then install telethon and request via pip: `pip install telethon requests`
1. Get your spotify client_id and your client_secret from https://developer.spotify.com/dashboard/. If you need more help, have a look [here](https://developer.spotify.com/documentation/general/guides/app-settings/#register-your-app).
2. Get your telegram app api_id and api_hash from https://my.telegram.org/. If you need more help, have a look [here](https://telethon.readthedocs.io/en/latest/extra/basic/creating-a-client.html#creating-a-client).
3. Open the following link (change CLIENT_ID to you client_id): https://accounts.spotify.com/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=https%3A%2F%2Fexample.com%2Fcallback&scope=user-read-playback-state%20user-read-currently-playing
4. After you grant permission, you get redirected to _https://example.com/callback?code=_. Copy everything after the code, this is you initial token.
5. Paste all these values in their respective variables at [constants.py](../master/constants.py). While you are at it, you can also paste an initial biography there. Just take your current one. This is highly recommended. If you don't do this **and** have a currently playing track, the bot has at its first start no idea what your original biography is. Just do it, please.
6. If you want to have a log channel or group or so, paste its invite link or id in the LOG variable. If you leave it at "me", you will see those in your saved chat. Only if errors accure ofc ;)
7. Now you can run [generate.py](../master/generate.py). This will generate a json file named database.
8. You are almost done. If you now run [bot.py](../master/bot.py), all you need to do is log into your account. Follow the instructions on screen.
9. Now you are really done.

## Issues? Need help? Want to tell me something?

Well, just create an issue here. You can also ping me on [telegram](https://t.me/poolitzer).
