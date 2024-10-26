import telebot
from telebot import types
import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI
import textwrap
import logging
import tempfile

#
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tgbot")

#
# You can set parse_mode by default. HTML or MARKDOWN
tb = telebot.TeleBot(os.environ.get("TELEGRAM_BOT_API_KEY"), parse_mode=None)
# tb.set_webhook()
tb.remove_webhook()

allowed_user_list = [item.strip() for item in os.environ.get("TELEGRAM_BOT_ALLOWED_USER_LIST").split(",")]
logger.info(f"allowed_user_list: {allowed_user_list}.")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    # organization=os.environ.get("OPENAI_API_ORGANIZATION"),
    # project=os.environ.get("OPENAI_API_PROJECT"),
)


@tb.message_handler(commands=['start'])
def send_welcome(message: types.Message):
    reply_message = None
    if message.chat.username not in allowed_user_list:
        reply_message = "Access denied " + message.chat.username + "!"
    else:
        reply_message = "Welcome to the club " + message.chat.username
    logger.info(reply_message)
    tb.reply_to(message, reply_message)


@tb.message_handler(func=lambda message: True)
def send_tts(message: types.Message):
    if message.chat.username not in allowed_user_list:
        reply_message = "Access denied " + message.chat.username + "!"
        tb.reply_to(message, reply_message)

    tb.reply_to(message, "Сообщение принято, преобразования")

    chat_id = message.chat.id

    speech_file = tempfile.NamedTemporaryFile(delete=False)
    logger.info(f"speech_file created: {speech_file.name}.")
    try:
        with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=message.text,
        ) as response:
            response.stream_to_file(speech_file.name)
        tb.send_audio(chat_id, speech_file)
    except:
        tb.reply_to(message, "Не удалось преобразовать текст в речь")
    finally:
        speech_file.close()
        os.unlink(speech_file.name)
        logger.info(f"speech_file unlinked: {speech_file.name}.")


tb.infinity_polling()
