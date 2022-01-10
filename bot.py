import asyncio
import os.path
import json
import logging

from aiohttp import ClientSession
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, AboutTooLongError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest

import constants
from setup import setup, intro_screen, update_constants

# values supplied to telegram
device_model = "spotify_bot"
version = "1.6"
system_version, app_version = version, version

# if the intro screen has already been printed
intro_printed = False

# this check allows the user to not having to enter any constants into constants.py prior to using this script
if constants.API_ID == 0:
    print(intro_screen)
    intro_printed = True
    constants.API_ID = int(
        input(
            "Hello there, thanks for using this little project. Please enter your Telegram App api_id. You can get"
            " it at https://my.telegran.org: "
        )
    )
    lines = [2]
    replacements = [f"API_ID = {constants.API_ID}"]
    # a bit better output strings, though its a bit weird if someone only enters one of the values
    if not constants.API_HASH:
        constants.API_HASH = input("\nGreat, now you need to copy paste the api_hash: ")
        lines.append(3)
        replacements.append(f'API_HASH = "{constants.API_HASH}"')
    update_constants(lines, replacements)
# again, weird if this is triggered, but who am I to judge
if not constants.API_HASH:
    print(intro_screen)
    intro_printed = True
    constants.API_HASH = input(
        "Hello there, thanks for using this little project. Please enter your Telegram App api_hash. You can get"
        " it at https://my.telegran.org: "
    )
    lines = [3]
    replacements = [f'API_HASH = "{constants.API_HASH}"']
    update_constants(lines, replacements)

client = TelegramClient(
    "spotify",
    constants.API_ID,
    constants.API_HASH,
    device_model=device_model,
    system_version=system_version,
    app_version=app_version,
)

logging.basicConfig(
    level=logging.ERROR,
    filename="log.log",
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

aiohttp_server_logger = logging.getLogger("aiohttp.server")
aiohttp_server_logger.disabled = True


def ms_converter(millis):
    millis = int(millis)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    if str(seconds) == "0":
        seconds = "00"
    if len(str(seconds)) == 1:
        seconds = "0" + str(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    return str(minutes) + ":" + str(seconds)


class Database:
    def __init__(self):
        try:
            self.db = json.load(open("./database.json"))
        except FileNotFoundError:
            # this will be the case when someone hasn't run the setup yet, it will be recalled when the file exists
            self.db = {}

    def save_token(self, token):
        self.db["access_token"] = token
        self.save()

    def save_refresh(self, token):
        self.db["refresh_token"] = token
        self.save()

    def save_bio(self, bio):
        self.db["bio"] = bio
        self.save()

    def save_spam(self, which, what):
        self.db[which + "_spam"] = what

    def return_token(self):
        return self.db["access_token"]

    def return_refresh(self):
        return self.db["refresh_token"]

    def return_bio(self):
        return self.db["bio"]

    def return_spam(self, which):
        return self.db[which + "_spam"]

    def save(self):
        with open("./database.json", "w") as outfile:
            json.dump(self.db, outfile, indent=4, sort_keys=True)


database = Database()


# to stop unwanted spam, we sent these type of message only once. So we have a variable in our database which we check
# for in return_info. When we send a message, we set this variable to true. After a successful update
# (or a closing of spotify), we reset that variable to false.
def save_spam(which, what):
    # see below why

    # this is if False is inserted, so if spam = False, so if everything is good.
    if not what:
        # if it wasn't normal before, we proceed
        if database.return_spam(which):
            # we save that it is normal now
            database.save_spam(which, False)
            # we return True so we can test against it and if it this function returns, we can send a fitting message
            return True
    # this is if True is inserted, so if spam = True, so if something went wrong
    else:
        # if it was normal before, we proceed
        if not database.return_spam(which):
            # we save that it is not normal now
            database.save_spam(which, True)
            # we return True so we can send a message
            return True
    # if True wasn't returned before, we can return False now so our test fails and we dont send a message
    return False


async def work(session: ClientSession):
    while True:
        # SPOTIFY
        skip = False
        to_insert = {}
        oauth = {"Authorization": "Bearer " + database.return_token()}
        async with session.get(
            "https://api.spotify.com/v1/me/player/currently-playing", headers=oauth
        ) as response:
            status_code = response.status
            # 200 means user plays smth
            if status_code == 200:
                received = await response.json()
                if received["currently_playing_type"] == "track":
                    to_insert["title"] = received["item"]["name"]
                    to_insert["progress"] = ms_converter(received["progress_ms"])
                    to_insert["interpret"] = received["item"]["artists"][0]["name"]
                    to_insert["duration"] = ms_converter(
                        received["item"]["duration_ms"]
                    )
                    if save_spam("spotify", False):
                        stringy = (
                            "**[INFO]**\n\nEverything returned back to normal, the previous spotify issue has been "
                            "resolved."
                        )
                        await client.send_message(constants.LOG, stringy)
                else:
                    if save_spam("spotify", True):
                        # currently item is not passed when the user plays a podcast
                        string = (
                            f"**[INFO]**\n\nThe playback {received['currently_playing_type']} didn't gave me any "
                            f"additional information, so I skipped updating the bio."
                        )
                        await client.send_message(constants.LOG, string)
            # 429 means flood limit, we need to wait
            elif status_code == 429:
                to_wait = response.headers["Retry-After"]
                logger.error(f"Spotify, have to wait for {str(to_wait)}")
                await client.send_message(
                    constants.LOG,
                    f"**[WARNING]**\n\nI caught a spotify api limit. I shall sleep for "
                    f"{str(to_wait)} seconds until I refresh again",
                )
                skip = True
                await asyncio.sleep(int(to_wait))
            # 204 means user plays nothing, since to_insert is false, we dont need to change anything
            elif status_code == 204:
                if save_spam("spotify", False):
                    stringy = (
                        "**[INFO]**\n\nEverything returned back to normal, the previous spotify issue has been "
                        "resolved."
                    )
                    await client.send_message(constants.LOG, stringy)
                pass
            # 401 means our access token is expired, so we need to refresh it
            elif status_code == 401:
                data = {
                    "client_id": constants.CLIENT_ID,
                    "client_secret": constants.CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": database.return_refresh(),
                }

                async with session.post(
                    "https://accounts.spotify.com/api/token", data=data
                ) as post_response:
                    received = await post_response.json()
                    # if a new refresh is token as well, we save it here
                    try:
                        database.save_refresh(received["refresh_token"])
                    except KeyError:
                        pass
                    database.save_token(received["access_token"])
                    # since we didnt actually update our status yet, lets do this without the 30 seconds wait
                    skip = True
            # 502 means bad gateway, its an issue on spotify site which we can do nothing about. 30 seconds wait
            # shouldn't put too much pressure on the spotify server, so we are just going to notify the user once
            elif status_code == 502:
                if save_spam("spotify", True):
                    string = (
                        f"**[WARNING]**\n\nSpotify returned a Bad gateway, which means they have a problem on their "
                        f"servers. The bot will continue to run but may not update the bio for a short time."
                    )
                    await client.send_message(constants.LOG, string)
            # 503 means service unavailable, its an issue on spotify site which we can do nothing about. 30 seconds wait
            # shouldn't put too much pressure on the spotify server, so we are just going to notify the user once
            elif status_code == 503:
                if save_spam("spotify", True):
                    string = (
                        f"**[WARNING]**\n\nSpotify said that the service is unavailable, which means they have a "
                        f"problem on their servers. The bot will continue to run but may not update the bio for a "
                        f"short time."
                    )
                    await client.send_message(constants.LOG, string)
            # 404 is a spotify error which isn't supposed to happen (since our URL is correct). Track the issue here:
            # https://github.com/spotify/web-api/issues/1280
            elif status_code == 404:
                if save_spam("spotify", True):
                    string = f"**[INFO]**\n\nSpotify returned a 404 error, which is a bug on their side."
                    await client.send_message(constants.LOG, string)
            # catch anything else
            else:
                await client.send_message(
                    constants.LOG,
                    "**[ERROR]**\n\nOK, so something went reeeally wrong with spotify. The bot "
                    "was stopped.\nStatus code: "
                    + str(status_code)
                    + "\n\nText: "
                    + await response.text(),
                )
                logger.error(
                    f"Spotify, error {str(status_code)}, text: {await response.text()}"
                )
                # stop the whole program since I dont know what happens here and this is the safest thing we can do
                asyncio.get_running_loop().stop()
            # TELEGRAM
            try:
                # full needed, since we dont get a bio with the normal request
                full = await client(GetFullUserRequest("me"))
                bio = full.about
                # to_insert means we have a successful playback
                if to_insert:
                    # putting our collected information's into nice variables
                    title = to_insert["title"]
                    interpret = to_insert["interpret"]
                    progress = to_insert["progress"]
                    duration = to_insert["duration"]
                    # we need this variable to see if actually one of the bios is below the character limit
                    new_bio = ""
                    for bio in constants.BIOS:
                        temp = bio.format(
                            title=title,
                            interpret=interpret,
                            progress=progress,
                            duration=duration,
                        )
                        # we try to not ignore for telegrams character limit here
                        if len(temp) < constants.LIMIT:
                            # this is short enough, so we put it in the variable and break our for loop
                            new_bio = temp
                            break
                    # if we have a bio, one bio was short enough
                    if new_bio:
                        # test if the user changed his bio to blank, we save it before we override
                        if not bio:
                            database.save_bio(bio)
                        # test if the user changed his bio in the meantime, if yes, we save it before we override
                        elif "🎶" not in bio:
                            database.save_bio(bio)
                        # test if the bio isn't the same, otherwise updating it would be stupid
                        if not new_bio == bio:
                            try:
                                await client(UpdateProfileRequest(about=new_bio))
                                if save_spam("telegram", False):
                                    stringy = (
                                        "**[INFO]**\n\nEverything returned back to normal, the previous telegram "
                                        "issue has been resolved."
                                    )
                                    await client.send_message(constants.LOG, stringy)
                            # this can happen if our LIMIT check failed because telegram counts emojis twice and python
                            # doesnt. Refer to the constants file to learn more about this
                            except AboutTooLongError:
                                if save_spam("telegram", True):
                                    stringy = (
                                        f"**[WARNING]**\n\nThe biography I tried to insert was too long. In order "
                                        f"to not let that happen again in the future, please read the part about OFFSET"
                                        f" in the constants. Anyway, here is the bio I tried to insert:\n\n{new_bio}"
                                    )
                                    await client.send_message(constants.LOG, stringy)
                    # if we dont have a bio, everything was too long, so we tell the user that
                    if not new_bio:
                        if save_spam("telegram", True):
                            to_send = (
                                f"**[INFO]**\n\nThe current track exceeded the character limit, so the bio wasn't "
                                f"updated.\n\n Track: {title}\nInterpret: {interpret}"
                            )
                            await client.send_message(constants.LOG, to_send)
                # not to_insert means no playback
                else:
                    if save_spam("telegram", False):
                        stringy = (
                            "**[INFO]**\n\nEverything returned back to normal, the previous telegram issue has "
                            "been resolved."
                        )
                        await client.send_message(constants.LOG, stringy)
                    old_bio = database.return_bio()
                    # this means the bio is blank, so we save that as the new one
                    if not bio:
                        database.save_bio(bio)
                    # this means an old playback is in the bio, so we change it back to the original one
                    elif "🎶" in bio:
                        await client(UpdateProfileRequest(about=database.return_bio()))
                    # this means a new original is there, lets save it
                    elif not bio == old_bio:
                        database.save_bio(bio)
                    # this means the original one we saved is still valid
                    else:
                        pass
            except FloodWaitError as e:
                to_wait = e.seconds
                logger.error(f"to wait for {str(to_wait)}")
                await client.send_message(
                    constants.LOG,
                    f"**[WARNING]**\n\nI caught a telegram api limit. I shall sleep "
                    f"{str(to_wait)} seconds until I refresh again",
                )
                skip = True
                await asyncio.sleep(int(to_wait))
            # skip means a flood error stopped the whole program, no need to wait another 30 seconds after that
            if not skip:
                await asyncio.sleep(30)


# little message that the bot was started
async def startup():
    await client.send_message(
        constants.LOG, "**[INFO]**\n\nUserbot was successfully started."
    )


# shutdown handler in case the bot goes nuts (again)
@client.on(events.NewMessage(outgoing=True, pattern=constants.SHUTDOWN_COMMAND))
async def shutdown_handler(_):
    logger.error("Initiating shut down")
    await client.send_message(
        constants.LOG, "**[INFO]**\n\nShutdown was successfully initiated."
    )
    # just so everything is saved - it should be anyway, but just to be sure
    database.save()
    # this stops the whole loop
    await client.disconnect()


async def main():
    await client.start()
    loop = asyncio.get_running_loop()
    async with ClientSession() as session:
        loop.create_task(work(session))
        loop.create_task(startup())
        await client.run_until_disconnected()


if __name__ == "__main__":
    if not os.path.isfile("./database.json"):
        asyncio.run(setup(intro_printed))
        # Reinitialize because json is only now generated
        database = Database()
    asyncio.run(main())
    logger.error("Shut down complete")
