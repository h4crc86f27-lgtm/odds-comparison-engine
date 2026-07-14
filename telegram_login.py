from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

api_id = 29423384
api_hash = "8e5a3c0c69708e9c61dadf04fd0eb678"

phone = "+31639413206"

client = TelegramClient("/home/arb_bot/@oddsbotalerts.session", api_id, api_hash)

client.connect()

if not client.is_user_authorized():
    client.send_code_request(phone)
    code = input("Telegram code: ")
    client.sign_in(phone, code)

print("\nSUCCESS!")
print(client.get_me())

client.disconnect()
