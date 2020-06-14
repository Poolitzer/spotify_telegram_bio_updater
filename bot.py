import asyncio
import time
from datetime import datetime
from constants import API_HASH, API_ID, SESSION_KEY, CLIENT_ID, CLIENT_SECRET, LOG, CMD_PREFIX, BIOS, LIMIT
import json
import logging
import requests
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, AboutTooLongError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEntityMentionName
from telethon.sessions import StringSession
device_model = "spotify_bot"
version = "1.5"
system_version, app_version = version, version

StartTime = time.time()


with TelegramClient(StringSession(SESSION_KEY), API_ID, API_HASH, device_model=device_model,
					system_version=system_version, app_version=app_version) as client:

					logging.basicConfig(level=logging.ERROR, filename='log.log',
					format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s')


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
		try:
			self.db = json.load(open("./database.json"))
		except FileNotFoundError:
			print("You need to run generate.py first, please read the Readme.")
			loop.stop()

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
		with open('./database.json', 'w') as outfile:
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
				to_insert["progress"] = ms_converter(received["progress_ms"])
				to_insert["interpret"] = received['item']["artists"][0]["name"]
				to_insert["duration"] = ms_converter(received["item"]["duration_ms"])
				to_insert["link"] = received['item']['external_urls']['spotify']
				to_insert["image"] = received['item']['album']['images'][1]['url']
				if save_spam("spotify", False):
					stringy = "**[INFO]**\n\nEverything returned back to normal, the previous spotify issue has been " \
							  "resolved."
					await client.send_message(LOG, stringy)
				   
			else:
				if save_spam("spotify", True):
					# currently item is not passed when the user plays a podcast
					string = f"**[INFO]**\n\nThe playback {received['currently_playing_type']} didn't gave me any " \
						f"additional information, so I skipped updating the bio."
					await client.send_message(LOG, string)
	   
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
			if save_spam("spotify", False):
				stringy = "**[INFO]**\n\nEverything returned back to normal, the previous spotify issue has been " \
						  "resolved."
				await client.send_message(LOG, stringy)
			pass
		# 401 means our access token is expired, so we need to refresh it
		elif r.status_code == 401:
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
			# since we didnt actually update our status yet, lets do this without the 30 seconds wait
			skip = True
		# 502 means bad gateway, its an issue on spotify site which we can do nothing about. 30 seconds wait shouldn't
		# put too much pressure on the spotify server, so we are just going to notify the user once
		elif r.status_code == 502:
			if save_spam("spotify", True):
				string = f"**[WARNING]**\n\nSpotify returned a Bad gateway, which means they have a problem on their " \
					f"servers. The bot will continue to run but may not update the bio for a short time."
				await client.send_message(LOG, string)
		# 503 means service unavailable, its an issue on spotify site which we can do nothing about. 30 seconds wait
		# shouldn't put too much pressure on the spotify server, so we are just going to notify the user once
		elif r.status_code == 503:
			if save_spam("spotify", True):
				string = f"**[WARNING]**\n\nSpotify said that the service is unavailable, which means they have a " \
						 f"problem on their servers. The bot will continue to run but may not update the bio for a " \
						 f"short time."
				await client.send_message(LOG, string)
		# 404 is a spotify error which isn't supposed to happen (since our URL is correct). Track the issue here:
		# https://github.com/spotify/web-api/issues/1280
		elif r.status_code == 404:
			if save_spam("spotify", True):
				string = f"**[INFO]**\n\nSpotify returned a 404 error, which is a bug on their side."
				await client.send_message(LOG, string)
		# catch anything else
		else:
			await client.send_message(LOG, '**[ERROR]**\n\nOK, so something went reeeally wrong with spotify. The bot '
										   'was stopped.\nStatus code: ' + str(r.status_code) + '\n\nText: ' + r.text)
			logger.error(f"Spotify, error {str(r.status_code)}, text: {r.text}")
			# stop the whole program since I dont know what happens here and this is the safest thing we can do
			loop.stop()
		# TELEGRAM
		try:
			# full needed, since we dont get a bio with the normal request
			full = await client(GetFullUserRequest('me'))
			bio = full.about
			# to_insert means we have a successful playback
			if to_insert:
				# putting our collected information's into nice variables
				
				title = to_insert["title"]
				interpret = to_insert["interpret"]
				progress = to_insert["progress"]
				duration = to_insert["duration"]
				work.interpret = to_insert["interpret"]
				work.progress = to_insert["progress"]
				work.duration = to_insert["duration"]
				work.title = to_insert["title"]
				work.link = to_insert["link"]
				work.image = to_insert["image"]
				# we need this variable to see if actually one of the bios is below the character limit
				new_bio = ""
				for bio in BIOS:
					temp = bio.format(title=title, interpret=interpret, progress=progress, duration=duration)
					# we try to not ignore for telegrams character limit here
					
					if len(temp) < LIMIT:
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
							work.lrt = time.time()
						   
							if save_spam("telegram", False):
								stringy = "**[INFO]**\n\nEverything returned back to normal, the previous telegram " \
										  "issue has been resolved."
								await client.send_message(LOG, stringy)
						# this can happen if our LIMIT check failed because telegram counts emojis twice and python
						# doesnt. Refer to the constants file to learn more about this
						except AboutTooLongError:
							if save_spam("telegram", True):
								stringy = f'**[WARNING]**\n\nThe biography I tried to insert was too long. In order ' \
									f'to not let that happen again in the future, please read the part about OFFSET ' \
									f'in the constants. Anyway, here is the bio I tried to insert:\n\n{new_bio}'
								await client.send_message(LOG, stringy)
				# if we dont have a bio, everything was too long, so we tell the user that
				if not new_bio:
					if save_spam("telegram", True):
						to_send = f"**[INFO]**\n\nThe current track exceeded the character limit, so the bio wasn't " \
							f"updated.\n\n Track: {title}\nInterpret: {interpret}"
						await client.send_message(LOG, to_send)
			# not to_insert means no playback
			else:
				if save_spam("telegram", False):
					stringy = "**[INFO]**\n\nEverything returned back to normal, the previous telegram issue has " \
							  "been resolved."
					await client.send_message(LOG, stringy)
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
			await client.send_message(LOG, f'**[WARNING]**\n\nI caught a telegram api limit. I shall sleep '
										   f'{str(to_wait)} seconds until I refresh again')
			skip = True
			await asyncio.sleep(int(to_wait))
		# skip means a flood error stopped the whole program, no need to wait another 30 seconds after that
		if not skip:
			await asyncio.sleep(30)

#------------------------------------------------PLUGINS--------------------------------------------------------#

@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "song"))
async def link_handler(event):
	oauth = {
			"Authorization": "Bearer " + database.return_token()}
	r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=oauth)
	if r.status_code == 204:
		spolink = "\n**I'm not playing anything right now :)**"
	else:
		spolink = f"""
🎶Playing: [{work.title}]({work.link}) - {work.interpret}
 """
	await event.edit(spolink,link_preview=True)

        
#-------------------------------------------?getsong---------------------------------------------------------#  
@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "help"))
async def help(event):
    CMD = CMD_PREFIX[1:]
    help_panel = f"""
**Currently available commands**
`{CMD}ping`: to check the ping.
`{CMD}status:` to check the status.
`{CMD}bio`: to check bio.
`{CMD}song`: to share the song's link which you're listening to on Spotify.
`{CMD}getsong`: to get current playing song's file(mp3).
`{CMD}restart`: to restart the bot.
    """
    await event.edit(help_panel,link_preview=True)
 
@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "getsong"))
async def get_song(event):
	oauth = {
			"Authorization": "Bearer " + database.return_token()}
	r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=oauth)
	if r.status_code == 204:
		spolink = await event.edit("\n**I'm not playing anything right now :)**")
	else:
		spolink = f"""{work.link}"""
		spotify_link = spolink[31:]
		chat = await event.client.get_entity("@spotify_to_mp3_bot")
		done = await event.edit("`Downloading..`")
		async with event.client.conversation(chat) as conv:
			try:
				await conv.send_message("/download spotify:track:{}".format(spotify_link))
				song = await conv.get_response()
				response = conv.wait_event(
					events.NewMessage(incoming=True, from_users=chat.id)
				)
				song = await response
				await event.client.send_read_acknowledge(
				entity=chat.id,
				message=song,
				clear_mentions=True
			)
				if song.audio:
					await done.delete()
					await event.client.send_message(event.chat_id, file=song.audio)
					
			except Exception as e:
				await event.reply(f"`RIP `: {str(e)}")
			return 
#---------------------------------------------------------------?ping--------------------------------------------

@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "ping"))
async def ping(event):
	start = datetime.now()
	await event.edit("pong!!")
	end = datetime.now()
	ms = (end - start).microseconds / 1000
	ping = f"**Pong\n{ms}**"
	await event.edit(ping)

#------------------------------------------------------------time_readable_funtion-------------------------------------

def get_readable_time(seconds: int) -> str:
	count = 0
	ping_time = ""
	time_list = []
	time_suffix_list = ["s", "m", "h", "days"]

	while count < 4:
		count += 1
		if count < 3:
			remainder, result = divmod(seconds, 60)
		else:
			remainder, result = divmod(seconds, 24)
		if seconds == 0 and remainder == 0:
			break
		time_list.append(int(result))
		seconds = int(remainder)

	for x in range(len(time_list)):
		time_list[x] = str(time_list[x]) + time_suffix_list[x]
	if len(time_list) == 4:
		ping_time += time_list.pop() + ", "

	time_list.reverse()
	ping_time += ":".join(time_list)

	return ping_time

#-----------------------------------------------------?alive----------------------------------------------------

@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "status"))
async def alive(event):  
	uptime = get_readable_time((time.time() - StartTime))
	alive_b = f"**Yes, Bot is running perfectly!**"
	alive_b += f"**\nBot uptime:**  {uptime}"
	oauth = {
			"Authorization": "Bearer " + database.return_token()}
	r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=oauth)
	if r.status_code == 204:
		alive_b += "\n**I'm not playing anything right now :)**"
	else:
		
		spotify_link = work.link
		spotify_link = spotify_link[31:]
		lrt = get_readable_time((time.time() - work.lrt))
		alive_b += f"\n**Last refresh:** {lrt} ago"
		alive_b += f"\n**Current playing song:** {work.title} - {work.interpret}"
		alive_b += f"\n**Spotify track id:** `{spotify_link}`"
		alive_b += f"\n**Duration:** {work.progress}/{work.duration}"
		
	await event.edit(alive_b)

#-----------------------------------------------------------?bio--------------------------------------------------   
  
@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "bio"))
async def bio_handler(event):
	me = await client.get_me()
	username = me.username
	full = await client(GetFullUserRequest(username))
	user_bio = full.about
	bio_s = f"**Bio:** {user_bio}"
	oauth = {
			"Authorization": "Bearer " + database.return_token()}
	r = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=oauth)
	if r.status_code == 204:
		bio_mode = "`Initial`"
	else:
		bio_mode = "`Spotify`"
		lrt = get_readable_time((time.time() - work.lrt))
		bio_s += f"\n**Last refresh:** {lrt} ago"
	bio_s += f"\n**Currently in {bio_mode} mode.**"
	await event.edit(bio_s)

# little message that the bot was started
async def startup():
	await client.send_message(LOG, "**[INFO]**\n\nSpotify was successfully started.")


# shutdown handler in case the bot goes nuts (again)
@client.on(events.NewMessage(outgoing=True, pattern=CMD_PREFIX + "restart"))
async def shutdown_handler(event):
	logger.error("SHUT DOWN")
	CMD = CMD_PREFIX[1:]
	await event.edit(f"**Restarted. `{CMD}ping` me or `{CMD}alive` to check if I am online**")
	await client.send_message(LOG, "**[INFO]**\n\nShutdown was successfully initiated.")
	# just so everything is saved - it should be anyway, but just to be sure
	database.save()
	# this stops the whole loop
	await client.disconnect()


client.start()
loop = asyncio.get_event_loop()
loop.create_task(work())
loop.create_task(startup())
client.run_until_disconnected()
