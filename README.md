# spotify_userbot
>This userbot updates the biography of a telegram user according to their current spotify playback. If no playback is active, the bot changes the bio back to the original one from the user.

## Available commands
`?ping:` to check the ping.

`?status:` to check the status.

`?bio:` to check bio.

`?song:` to share the song's link which you're listening to on Spotify.

`?getsong:` to get current playing song's file(mp3).

`?restart:` to restart the bot.

## Setup

If you follow this steps, you can use this project easily for yourself.

### Ensure you have python 3.6+ installed and then install telethon and request via pip: `pip install telethon requests`

-  Get your spotify client_id and your client_secret from [here](https://developer.spotify.com/dashboard/). 

-  Get your telegram app api_id and api_hash from `my.telegram.org`. 

-  Click [here](https://accounts.spotify.com/authorize?client_id=CLIENT_ID&response_type=code&redirect_uri=https%3A%2F%2Fexample.com%2Fcallback&scope=user-read-playback-state%20user-read-currently-playing) (change CLIENT_ID to you client_id): 

-  After you grant permission, you get redirected to `https://example.com/callback?code=_`. Copy everything after the code, this is you initial token.

-  Paste all these values in their respective variables at [constants.py](/constants.py). While you are at it, you can also paste an initial biography there. Just take your current one. This is highly recommended. If you don't do this **and** have a currently playing track, the bot has at its first start no idea what your original biography is. Just do it, please.

- If you want to have a log channel or group or so, paste its invite link or id in the LOG variable. If you leave it at "me", you will see those in your saved chat. Only if errors occur ofc ;)

-  Now you can run [generate.py](/generate.py). This will generate a json file named database.

-  You are almost done. If you now run [bot.py](/bot.py), all you need to do is log into your telegram account. Follow the instructions on screen.
-  Now you are really done.

## Warning

This bot uses the emoji 🎶 to determine if the current bio is an active spotify biography or not. This means you mustn't use this emoji on your original biographies or the bot will probably break. Don't do it, thanks.

## But I want to

Great news. Just change the KEY variable in [constants](/constants.py) file. Don't ever use your new KEY in your biographies though!

### Credits:
[@Poolitzer](https://github.com/Poolitzer) (for creating this userbot.)

[@sunnyXdm](https://github.com/sunnyXdm) (for ?getsong feature) 

