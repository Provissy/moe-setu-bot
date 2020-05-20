import configparser
import logging
# from flask import Flask, request
from time import sleep
from telegram.ext import Updater, Dispatcher, MessageHandler, CommandHandler, Filters, InlineQueryHandler
import requests
import shlex
from pixivpy3 import *
from helper import *
from commands import *
from state_control import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# _ Define updater and pixiv apis.
# updater = Updater(TOKEN,request_kwargs=REQUEST_KWARGS, use_context=True)
updater = None
dispatcher = None
pixiv_api = None


# _ Various methods to process received messages.
def process_command(update, context):
    text = update.message.text
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! CHAT ID IS: ", update.effective_chat.id)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! CHAT TEXT IS: ", update.message.text)

    if text.startswith("/help") or text.startswith("help"):
        command_help(update, context)

    elif text.startswith("/identify") or text.startswith("identify"):
        command_identify(update, context)

    elif text.startswith("/echo") or text.startswith("echo"):
        update.message.reply_text(text)

    elif text.startswith("/upscale") or text.startswith("upscale"):
        update.message.reply_text("Not implemented yet!")

    elif text.startswith("/pixiv") or text.startswith("pixiv"):
        command_pixiv(update, context, pixiv_api)

    elif text.startswith("/"):
        update.message.reply_text("Sorry, unknown command, please use /help to list available commands.")

    else:
        pass


def process_photo(update, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! PHOTO RECEIVED")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ID0 IS: ", update.message.photo[0].file_id)
    # Check if the photo is eligible for identifying. If so, process it.
    if update.message.from_user.id in StateControl.list_user_waiting_identify:
        # DO NOT use reply_text, PhotoMessage does not support it.
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id,
                                 text="Identifying...\n識別中...\nUID: " + str(update.message.from_user.id))
        parsed_result = identify_photo(update.message.from_user.id, update.message.photo[0].file_id, context)
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id,  text=parsed_result)


def process_reply(update, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! REPLY MSG RECEIVED")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! IS REPLY TO IS: ", update.message.reply_to_message.message_id)
    # Check if is replying to a photo
    if update.message.reply_to_message.photo is not None:
        if update.message.from_user.id in StateControl.list_user_waiting_identify:
            update.message.reply_text("Please wait until current operation is done!")
            return

        StateControl.list_user_waiting_identify.append(update.message.from_user.id)
        if update.message.text.startswith("identify") or update.message.text.startswith("/identify"):
            context.bot.send_message(chat_id=update.effective_chat.id, text="Identifying...\n識別中...\nUID: " + str(update.message.from_user.id))
            parsed_result = identify_photo(update.message.from_user.id, update.message.reply_to_message.photo[0].file_id, context)
            context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id, text=parsed_result)



# _ Main entry.
def main():
    # _ Load configurations
    config = configparser.ConfigParser()
    config.read('config.ini')
    GlobalConst.TOKEN = config['TELEGRAM']['ACCESS_TOKEN']
    GlobalConst.SAUCENAO_API = config['TELEGRAM']['SAUCENAO_API']
    GlobalConst.SAUCENAO_URL = 'https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=16&api_key='
    GlobalConst.PIXIV_USER = config['PIXIV']['USERNAME']
    GlobalConst.PIXIV_PASS = config['PIXIV']['PASSWORD']
    GlobalConst.IMG_SERVER_ADDR = config['MISC']['IMG_SERVER_ADDR']
    # Notify user to verify the configs.
    print("Your token is: ", GlobalConst.TOKEN)
    print("Your saucenao api is: ", GlobalConst.SAUCENAO_URL)
    print("Your image server address is: ", GlobalConst.IMG_SERVER_ADDR)
    # _ Initialise bot and pixiv api
    global updater
    updater = Updater(GlobalConst.TOKEN, use_context=True)
    global dispatcher
    dispatcher = updater.dispatcher
    global pixiv_api
    pixiv_api = AppPixivAPI()

    dispatcher.add_handler(MessageHandler(Filters.reply, process_reply))
    dispatcher.add_handler(MessageHandler(Filters.text,  process_command))
    dispatcher.add_handler(MessageHandler(Filters.photo, process_photo))


    # Log into Pixiv.
    pixiv_api.login(GlobalConst.PIXIV_USER, GlobalConst.PIXIV_PASS)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Logged into pixiv successfully")

    # dispatcher.add_handler(CommandHandler('identify', command_identify))

    print("Starting polling...")

    updater.start_polling()
    updater.idle()

    print("PROGRAMME EXITED")


if __name__ == '__main__':
    main()

###################
# Codes below reserved for future WebHook implementation.
###################


# Initial Flask app
# app = Flask(__name__)

## Initial bot by Telegram access token
# bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))
#
#
# @app.route('/hook', methods=['POST'])
# def webhook_handler():
#    """Set route /hook with POST method will trigger this method."""
#    if request.method == "POST":
#        update = telegram.Update.de_json(request.get_json(force=True), bot)
#
#        # Update dispatcher process that handler to process this message
#        dispatcher.process_update(update)
#    return 'ok'
#
#
# def reply_handler(bot, update):
#    """Reply message."""
#    text = update.message.text
#    update.message.reply_text(text)
#

# New a dispatcher for bot
# dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.
# dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

# if __name__ == "__main__":
#    # Running server
#    app.run(debug=True)
