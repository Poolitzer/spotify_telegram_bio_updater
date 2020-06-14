CLIENT_ID = "4b30d73291cf4696bdfc92e7bec764b8"
CLIENT_SECRET = "8c4c48615a9e433a80519b269a14c005"
API_ID = 648051
API_HASH = "8b76366d0ef72f3bed68ec45d37cd1fd"
SESSION_KEY = "1BVtsOMYBuzcs6gY2NgjqIg2iVhzKlPCQzRGBZoOkFjDrubSsyonQzV7Ika46f7UFrI4hKsl68wZOrry-YL_aAEadlU6MgyMgHWOCPfYDm82TbWlfLzaVczhrYgkurF7Bi86BfDahSVszBL63F1AHNW7OAFMA0qu3upRketqTj25rwEKBeE0U7GKI5Cs_lUv2Tk9Thr1W8fCQSv4czhTuaxlB1J9NISNvGNVJP6PNz5Ak01QmBMvNZBsbuUOWC_RdJsfv-XySr3gb0Y4SJueiGYmcFmcw-oU10rYmgbrsvMgr6Ozxq-xBHJzR_1wF55FXHSiUwHQ6KQf39lY7oQsL0HoxPks86pQ="
INITIAL_TOKEN = "AQBxJoEvlhXpLhLI8v0aBnW4MUu567uHyM9EAdvDo4d7W6MqvDguN2vkSct1OyQfahJZQjsn8xYN2D1VnUPhuECBb3MXQxyhIMK0G80b19MNd8id51pA-ZsPkmRZ5Jcr-TE5GbigfAuvglz5I9mbP0uzvN2cTvX-I-mmqj-XJi3Rdoaq453vS7xlTxgd3kP_NcfNKDwzElJujdNW1pdqlW7Gajqvy5VyhdQo-dPcNmF8pKYsCtPc"
INITIAL_BIO = "Existence is painfull! Zoldyck Family™♥️//Spam here @MedevilofMarvel"
LOG = -1001477891420
# the escaping is necessary since we are testing against a regex pattern with it.
CMD_PREFIX = '\?' 
# The key which is used to determine if the current bio was generated from the bot ot from the user. This means:
# NEVER use whatever you put here in your original bio. NEVER. Don't do it!
KEY = '🎶'
# The bios MUST include the key. The bot will go though those and check if they are beneath telegrams character limit.
BIOS = [KEY + ' Listening with Parisa ^^: {interpret} - {title} {progress}/{duration}',
        KEY + ' Listening with Parisa ^^: {interpret} - {title}',
        KEY + ' : {interpret} - {title}',
        KEY + ' Listening with Parisa ^^: {title}',
        KEY + ' : {title}']
# Mind that some characters (e.g. emojis) count more in telegram more characters then in python. If you receive an
# AboutTooLongError and get redirected here, you need to increase the offset. Check the special characters you either
# have put in the KEY or in one of the BIOS with an official Telegram App and see how many characters they actually
# count, then change the OFFSET below accordingly. Since the standard KEY is one emoji and I don't have more emojis
# anywhere, it is set to one (One emoji counts as two characters, so I reduce 1 from the character limit).
OFFSET = 1
# reduce the OFFSET from our actual 70 character limit
LIMIT = 70 - OFFSET
