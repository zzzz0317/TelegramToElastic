from config import *
from telethon import TelegramClient, utils

telegram_client = TelegramClient('anon', TELEGRAM_API_ID, TELEGRAM_API_HASH, proxy=TELEGRAM_PROXY)


async def main():
    non_archived = await telegram_client.get_dialogs()
    # print(non_archived[0].stringify())
    # print(getattr(non_archived[0], 'name', ''))
    for chat in non_archived:
        chat_name = getattr(chat, 'name', '')
        chat_message = getattr(chat, 'message', '')
        peer_id = getattr(chat_message, 'peer_id', '')
        print("chat_name:{}\tpeer_id:{}".format(chat_name, utils.get_peer_id(peer_id)))
        print("peed_info:{}\n".format(peer_id))


if __name__ == '__main__':
    with telegram_client:
        telegram_client.loop.run_until_complete(main())
