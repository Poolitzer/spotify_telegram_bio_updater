import asyncio
from constants import API_HASH, API_ID, CLIENT_ID, CLIENT_SECRET, LOG, SHUTDOWN_COMMAND
import json
import logging
import requests
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest
device_model = "spotify_bot"
version = "1.3"
system_version, app_version = version, version
client = TelegramClient('spotify', API_ID, API_HASH, device_model=device_model,
                        system_version=system_version, app_version=app_version)
logging.basicConfig(level=logging.ERROR, filename='log.log')
logger = logging.getLogger(__name__)


def ms_converter(millis):
    millis = int(millis)
    seconds = (millis/1000) % 60
    seconds = int(seconds)
    if str(seconds) == '0':
        seconds = '00'
    if len(str(seconds)) == 1:
        seconds = '0' + str(seconds)
    minutes = (millis/(1000*60)) % 60
    minutes = int(minutes)
    return str(minutes) + ":" + str(seconds)


class Database:
    def __init__(self):
        self.db = json.load(open("./database.json"))

    def save_token(self, token):
        self.db["access_token"] = token
        self.save()

    def save_refresh(self, token):
        self.db["refresh_token"] = token
        self.save()

    def save_bio(self, bio):
        self.db["bio"] = bio
        self.save()

    def save_info(self, insert):
        self.db["info"] = insert

    def return_token(self):
        return self.db["access_token"]

    def return_refresh(self):
        return self.db["refresh_token"]

    def return_bio(self):
        return self.db["bio"]

    def return_info(self):
        return self.db["info"]

    def save(self):
        with open('./database.json', 'w') as outfile:
            json.dump(self.db, outfile, indent=4, sort_keys=True)


database = Database()


async def work():
    while True:
        # SPOTIFY
        skip = False
        to_insert = {}
        oauth = {
            "Authorization": "Bearer " + database.return_token()}
        r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=oauth)
        # 200 means user plays smth
        if r.status_code == 200:
            received = r.json()
            if received["currently_playing_type"] == "track":
                to_insert["title"] = received["item"]["name"]
                to_insert["done"] = ms_converter(received["progress_ms"])
                to_insert["artist"] = received['item']["artists"][0]["name"]
                to_insert["duration"] = ms_converter(received["item"]["duration_ms"])
            else:
                # currently item is not passed when the user plays a podcast
                await client.send_message(LOG, f"**[INFO]**\n\nThe playback {received['currently_playing_type']} didn't"
                                               f" gave me any additional information, so I skipped updating the bio.")
                # to stop unwanted spam, we sent this only once. After a successful update (or a closing of spotify), we
                # reset that
                database.save_info(True)
        # 429 means flood limit, we need to wait
        elif r.status_code == 429:
            to_wait = r.headers['Retry-After']
            logger.error(f"Spotify, have to wait for {str(to_wait)}")
            await client.send_message(LOG, f'**[WARNING]**\n\nI caught a spotify api limit. I shall sleep for '
                                           f'{str(to_wait)} seconds until I refresh again')
            skip = True
            await asyncio.sleep(int(to_wait))
        # 204 means user plays nothing, since to_insert is false, we dont need to change anything
        elif r.status_code == 204:
            pass
        # catch anything else and stop the whole program since I dont know what happens here
        else:
            await client.send_message(LOG, '**[ERROR]**\n\nOK, so something went reeeally wrong with spotify.'
                                           '\nStatus code: ' + str(r.status_code) + '\n\nText: ' + r.text)
            logger.error(f"Spotify, error {str(r.status_code)}, text: {r.text}")
            loop.stop()
        # TELEGRAM
        try:
            # full needed, since we dont get a bio with the normal request
            full = await client(GetFullUserRequest('me'))
            bio = full.about
            # to_insert means we have a successful playback
            if to_insert:
                # testing for the 70 character limit, 69 since the emoji counts two times for telegram
                string = '🎶 Now Playing: ' + to_insert["artist"] + ' - ' + to_insert["title"] + ' ' \
                         + to_insert["done"] + '/' + to_insert["duration"]
                if len(string) > 69:
                    string = '🎶 Now Playing: ' + to_insert["artist"] + ' - ' + to_insert["title"]
                if len(string) > 69:
                    string = '🎶 : ' + to_insert["artist"] + ' - ' + to_insert["title"]
                if len(string) > 69:
                    string = '🎶 Now Playing: ' + to_insert["title"]
                if len(string) > 69:
                    string = '🎶 : ' + to_insert["title"]
                # everything fails, we notify the user that we can't update
                if len(string) > 69:
                    to_send = f"**[INFO]**\n\nThe current track exceeded the character limit, so the bio wasn't " \
                        f"updated.\n\n Track: {to_insert['title']}\nInterpret: {to_insert['artist']}"
                    await client.send_message(LOG, to_send)
                    # see line 91-92
                    database.save_info(True)
                else:
                    # test if the user changed his bio in the meantime
                    if "🎶" not in bio:
                        database.save_bio(bio)
                    # test if the bio isn't the same
                    if not string == bio:
                        await client(UpdateProfileRequest(about=string))
                        # see line 91-92 why
                        database.save_info(False)
            # not to_insert means no playback
            else:
                # see line 91-92 why
                database.save_info(False)
                old_bio = database.return_bio()
                # this means an old playback is in the bio, so we change it back to the original one
                if "🎶" in bio:
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
            await client.send_message(LOG, f'**[WARNING]**\n\nI caught a telegram api limit. I shall sleep '
                                           f'{str(to_wait)} seconds until I refresh again')
            skip = True
            await asyncio.sleep(int(to_wait))
        # Im not sure if this skip actually works or the task gets repeated after the sleep, but it doesn't hurt ;P
        if not skip:
            await asyncio.sleep(30)


# this refresh is needed since the access token expires after some hours.
async def refresh():
    data = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": database.return_refresh()}
    r = requests.post("https://accounts.spotify.com/api/token", data=data)
    received = r.json()
    # if a new refresh is token as well, we save it here
    try:
        database.save_refresh(received["refresh_token"])
    except KeyError:
        pass
    database.save_token(received["access_token"])
    await asyncio.sleep(received["expires_in"])


# little message that the bot was started
async def startup():
    await client.send_message(LOG, "**[INFO]**\n\nUserbot was successfully started.")


# shutdown handler in case the bot foes nuts (again)
@client.on(events.NewMessage(outgoing=True, pattern=SHUTDOWN_COMMAND))
async def shutdown_handler(_):
    logger.error("SHUT DOWN")
    await client.send_message(LOG, "**[INFO]**\n\nShutdown was successfully initiated.")
    await client.disconnect()


client.start()
loop = asyncio.get_event_loop()
loop.create_task(refresh())
loop.create_task(work())
loop.create_task(startup())
client.run_until_disconnected()
