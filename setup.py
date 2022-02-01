import re
import asyncio
import json

from aiohttp import ClientSession, web

import constants


# a nice intro screen when an input is required
intro_screen = (
    "\n|----------------------------|\n"
    "|Spotify_Telegram_Bio_Updater|\n"
    "|----------------------------|\n"
)


# this function rewrites constants.py and replaces the desired change_lines
def update_constants(change_lines: [int], replacement: [str]):
    with open("./constants.py", "r", encoding="UTF-8") as file:
        # read a list of change_lines into data
        data = file.readlines()
    # now change the 2nd line, note that you have to add a newline
    for index, line in enumerate(change_lines):
        data[line] = replacement[index] + "\n"

    # and write everything back
    with open("./constants.py", "w", encoding="UTF-8") as file:
        file.writelines(data)


async def setup(intro_printed: bool):
    if not intro_printed:
        print(intro_screen)
        print("Hello there, thanks for using this little project. ")
    replace_lines = []
    replacement_strings = []
    if constants.KEY == "🎶":
        new_key = input(
            "The default bio key is the emoji 🎶. The key is used to check if the current bio is set by you or from "
            "this script. This means you MUSTN'T use the key in your own bio.\nIf you want to change the key, enter "
            "the new one, otherwise just hit enter: "
        )
        if new_key:
            constants.KEY = new_key
            replace_lines.append(11)
            replacement_strings.append(f'KEY = "{constants.KEY}"')
    if not constants.INITIAL_BIO:
        constants.INITIAL_BIO = input(
            "Please paste here your current Telegram Biography (remember to not have the key in there): "
        )
        replace_lines.append(5)
        replacement_strings.append(f'INITIAL_BIO = "{constants.INITIAL_BIO}"')
    if constants.LOG == "me":
        new_log = input(
            "Every error will be logged in a telegram chat. The default one is your Saved Messages one, if you want to "
            "pick another, enter it here. The best working formats are either the username or invitation link of the "
            "chat. Otherwise, just hit enter and your Saved Messages chat will be used. "
        )
        if new_log:
            constants.LOG = new_log
            replace_lines.append(6)
            replacement_strings.append(f'LOG = "{constants.LOG}"')
    if constants.SHUTDOWN_COMMAND == "\/\/stop":
        new_shutdown = input(
            "This project has a shutdown command, which every message you send anywhere is checked against. It "
            "defaults to //stop, if you want to change this, enter the new shutdown command here, otherwise "
            "just press enter: "
        )
        if new_shutdown:
            constants.SHUTDOWN_COMMAND = re.escape(new_shutdown)
            replace_lines.append(8)
            replacement_strings.append(
                f'SHUTDOWN_COMMAND = "{constants.SHUTDOWN_COMMAND}"'
            )
    if not constants.CLIENT_ID:
        constants.CLIENT_ID = input(
            "Now your Spotify Client ID is needed, you can get it from https://developer.spotify.com/dashboard/. "
            "Make sure to add the Redirect URI http://localhost:1234/callback, otherwise you will see the error "
            "INVALID_CLIENT: Invalid redirect URI. "
        )
        replace_lines.append(0)
        replacement_strings.append(f'CLIENT_ID = "{constants.CLIENT_ID}"')
        if not constants.CLIENT_SECRET:
            constants.CLIENT_SECRET = input(
                "From the same site, copy paste your Client Secret: "
            )
            replace_lines.append(1)
            replacement_strings.append(f'CLIENT_SECRET = "{constants.CLIENT_SECRET}"')
    if not constants.CLIENT_SECRET:
        constants.CLIENT_SECRET = input(
            "When you added the Spotify Client ID, you forgot to add the Client Secret.\n"
            "Make sure that you set the Redirect URI http://localhost:1234/callback, otherwise you will see the error "
            "INVALID_CLIENT: Invalid redirect URI. "
        )
        replace_lines.append(1)
        replacement_strings.append(f'CLIENT_SECRET = "{constants.CLIENT_SECRET}"')
    update_constants(replace_lines, replacement_strings)
    if not constants.INITIAL_TOKEN:
        print(
            f"Great. Now you have to open the following URL, and connect your account to your Spotify Client. After "
            f"you have done that, you will be greeted by an Internal Server error, that is expected because the "
            f"local web server is killed immediately.\nJust return to this window for the next steps: "
            f"https://accounts.spotify.com/authorize?client_id={constants.CLIENT_ID}&response_type=code&"
            "redirect_uri=http://localhost:1234/callback&scope=user-read-playback-state%20"
            "user-read-currently-playing\nIf you see the INVALID_CLIENT: Invalid redirect URI, you need to set "
            "http://localhost:1234/callback as an URI in your client, and restart this project (your config has been "
            "saved no worries)."
        )
        app = web.Application()
        runner = web.AppRunner(app)
        loop = asyncio.get_running_loop()
        running = loop.create_future()
        app["future"] = running
        app.add_routes([web.get("/callback", code_getter)])
        await runner.setup()
        site = web.TCPSite(runner, host="localhost", port=1234)
        await site.start()
        try:
            await running
        except IndexError:
            pass
    async with ClientSession() as session:
        data = {
            "client_id": constants.CLIENT_ID,
            "client_secret": constants.CLIENT_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:1234/callback",
            "code": constants.INITIAL_TOKEN,
        }
        async with session.post(
            "https://accounts.spotify.com/api/token", data=data
        ) as post_response:
            save = await post_response.json()
            to_create = {
                "bio": constants.INITIAL_BIO,
                "access_token": save["access_token"],
                "refresh_token": save["refresh_token"],
                "telegram_spam": False,
                "spotify_spam": False,
            }
            with open("./database.json", "w") as outfile:
                json.dump(to_create, outfile, indent=4, sort_keys=True)
    print(
        "\nThe initial setup run successfully, now you need to sign into your Telegram account.\n"
    )


async def code_getter(request):
    constants.INITIAL_TOKEN = request.rel_url.query["code"]
    await request.app["future"].set_exception(IndexError)
