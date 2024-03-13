from config import *
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.errors.rpcerrorlist import PeerIdInvalidError, ChannelInvalidError, ChannelPrivateError
from telethon.utils import get_display_name
import asyncio
import FileDict
import time
from loguru import logger

telegram_client = TelegramClient('anon', TELEGRAM_API_ID, TELEGRAM_API_HASH, proxy=TELEGRAM_PROXY)
elasticsearch = ELASTICSEARCH_CLIENT


async def login():
    while True:
        try:
            await telegram_client.connect()
            logger.info("telegram_client connected")
            if not await telegram_client.is_user_authorized():
                logger.error("User not authorized")
                time.sleep(0.1)
                phone = input("Please enter your phone: ")
                await telegram_client.send_code_request(phone)
                code = input('Enter code: ')
                try:
                    await telegram_client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    await telegram_client.sign_in(password=input('Enter password: '))
            else:
                logger.info("User is authorized")
                break
        except Exception as e:
            logger.error(e)


async def main():
    me = await telegram_client.get_me()
    logger.info("CurrentUser:\tUser.id={}\tUser.username={}\tUser.first_name={}\tUser.last_name={}\t",
                me.id,
                me.username,
                me.first_name,
                me.last_name,
                me.phone
                )


async def main_loop():
    while True:
        for chat_id in TELEGRAM_CHAT_LIST:
            latest_chat_message_id = get_latest_chat_message_id(chat_id)
            logger.info("Get message from chat #{}, offset={}", chat_id, latest_chat_message_id)
            await process_telegram_chat_message(chat_id, latest_chat_message_id, TELEGRAM_PULL_ONCE)
        logger.info("Sleep {}s", TELEGRAM_PULL_SLEEP_SEC)
        time.sleep(TELEGRAM_PULL_SLEEP_SEC)


async def print_message(chat_id, message):
    chat = await message.get_chat()
    sender = await message.get_sender()
    text = "=" * 20
    text += "\nMSG #{}\n".format(message.id)
    text += "CHAT: #{} {}\n".format(chat_id, get_display_name(chat))
    text += "USER: #{} {} {}\n".format(getattr(sender, 'id', ''),
                                       getattr(sender, 'first_name', ''),
                                       getattr(sender, 'last_name', ''))
    text += "TIME: {}\n".format(message.date)
    text += "TEXT: {}\n".format(message.message)
    text += "=" * 20
    text += "\n"
    logger.info(text)


async def format_message_for_elasticsearch(chat_id, message):
    if not message.text:
        return None
    chat = await message.get_chat()
    chat_display_name = get_display_name(chat)
    sender = await message.get_sender()
    doc = {
        "message_id": message.id,
        "chat_name": chat_display_name,
        "chat_id": chat_id,
        "sender": {
            "user_id": getattr(sender, 'id', ''),
            "user_name": getattr(sender, 'username', ''),
            "user_firstname": getattr(sender, 'first_name', ''),
            "user_lastname": getattr(sender, 'last_name', '')
        },
        "timestamp": message.date,
        "text": message.text
    }
    return doc


async def save_to_elasticsearch(chat_id, message):
    if not message:
        return
    doc_data = await format_message_for_elasticsearch(chat_id, message)
    if not doc_data:
        return
    logger.debug(doc_data)
    index_id = "{}.{}".format(chat_id, message.id)
    elasticsearch.index(index=ELASTICSEARCH_INDEX, id=index_id, document=doc_data)
    save_latest_chat_message_id(chat_id, message.id)
    log_info = "msg #{} from \"{}\" by \"{}\": {}".format(
        index_id,
        doc_data["chat_name"],
        doc_data["sender"]["user_firstname"],
        doc_data["text"].split("\n"))
    logger.info('Submitted {}', log_info)


async def process_telegram_chat_message(chat_id, offset_id, limit=1000):
    try:
        entity = await telegram_client.get_entity(chat_id)
        async for message in telegram_client.iter_messages(entity, reverse=True, offset_id=offset_id, limit=limit):
            # await print_message(chat_id, message)
            await save_to_elasticsearch(chat_id, message)
    except ChannelInvalidError as e:
        TELEGRAM_CHAT_LIST.remove(chat_id)
        logger.error("Channel Invalid Error #{} reported by telethon ({}). We'll resume collecting in 5 seconds", chat_id, e)
        logger.error("We'll remove this entity and resume collecting in 5 seconds.")
        time.sleep(5)
    except ChannelPrivateError as e:
        TELEGRAM_CHAT_LIST.remove(chat_id)
        logger.error("Channel Private Error #{} reported by telethon ({}). We'll resume collecting in 5 seconds", chat_id, e)
        logger.error("We'll remove this entity and resume collecting in 5 seconds.")
        time.sleep(5)
    except PeerIdInvalidError as e:
        logger.error("Invalid peer #{} reported by telethon ({}). We'll resume collecting in 5 seconds", chat_id, e)
        logger.error("We'll skip this entity and resume collecting in 5 seconds.")
        time.sleep(5)
    except ValueError as e:
        logger.error("Invalid peer #{} reported by telethon ({}).", chat_id, e)
        logger.error("We'll skip this entity and resume collecting in 5 seconds.")
        time.sleep(5)


def init_latest_channel_message_id():
    """从文本中读取到最新保存到es的id并更新到变量"""
    try:
        latest_dict = FileDict.load_obj('latest_id')
        # print("历史记录: {}".format(latest_dict))
        for chat_id in TELEGRAM_CHAT_LIST:
            if chat_id in latest_dict:
                TELEGRAM_CHAT_LATEST_MSG_ID[chat_id] = latest_dict[chat_id]
    except FileNotFoundError as e:
        logger.info("latest_id not found.")


def save_latest_chat_message_id(chat_id, msg_id):
    TELEGRAM_CHAT_LATEST_MSG_ID[chat_id] = msg_id
    FileDict.save_obj(TELEGRAM_CHAT_LATEST_MSG_ID, 'latest_id')


def get_latest_chat_message_id(chat_id):
    return TELEGRAM_CHAT_LATEST_MSG_ID[chat_id]


if __name__ == '__main__':
    logger.debug("DEBUG Log is enabled!")
    init_latest_channel_message_id()
    logger.info("Chat list: {}", TELEGRAM_CHAT_LIST)
    logger.info("Chat latest message id: {}", TELEGRAM_CHAT_LATEST_MSG_ID)
    asyncio.get_event_loop().run_until_complete(login())
    logger.warning("Synchronization will start in 5 seconds")
    time.sleep(5)
    with telegram_client:
        telegram_client.loop.run_until_complete(main())
        telegram_client.loop.run_until_complete(main_loop())
