from telethon.sync import TelegramClient
from telethon.sessions import StringSession
with TelegramClient(StringSession(), API_ID, API_HASH) as c:
    print(c.session.save())