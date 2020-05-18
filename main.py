import os
import argparse
import datetime
import configparser
import logging
# from flask import Flask, request
from time import sleep

from telegram.ext import Updater, Dispatcher, MessageHandler, CommandHandler, Filters, InlineQueryHandler
import requests
import shlex
from pixivpy3 import *
from helper import *

# Defines constants.
# Load data from config.ini file

config = configparser.ConfigParser()
config.read('config.ini')
# REQUEST_KWARGS={ 'proxy_url': 'http://127.0.0.1:8118/', }
TOKEN = config['TELEGRAM']['ACCESS_TOKEN']
SAUCENAO_API = config['TELEGRAM']['SAUCENAO_API']
SAUCENAO_URL = 'https://saucenao.com/search.php?db=999&output_type=2&testmode=1&numres=16&api_key='
PIXIV_USER:str = config['PIXIV']['USERNAME']
PIXIV_PASS:str = config['PIXIV']['PASSWORD']
IMG_SERVER_ADDR:str = config['MISC']['IMG_SERVER_ADDR']

# Global state control.
list_user_waiting_identify = []

# Notify user to verify the configs.
print("Your token is: ", TOKEN)
# print("Your proxy address is set to: ", REQUEST_KWARGS)
print("Your saucenao api is: ", SAUCENAO_API)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# _ Initialise updater and pixiv apis.
# updater = Updater(TOKEN,request_kwargs=REQUEST_KWARGS, use_context=True)
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher
pixiv_api = AppPixivAPI()


# _ Various methods to process received messages.
def process_command(update, context):
    text = update.message.text
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! CHAT ID IS: ", update.effective_chat.id)
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! CHAT TEXT IS: ", update.message.text)

    if text.startswith("/help"):
        command_help(update, context)

    elif text.startswith("/identify"):
        command_identify(update, context)

    elif text.startswith("/echo"):
        update.message.reply_text(text)

    elif text.startswith("/upscale"):
        update.message.reply_text("Not implemented yet!")

    elif text.startswith("/pixiv"):
        command_pixiv(update, context)

    elif text.startswith("/debug"):
        command_debug(update, context)

    elif text.startswith("/"):
        update.message.reply_text("Sorry, unknown command, please use /help to list available commands.")

    else:
        pass


def command_debug(update, context):
    if "photo" in update.message.text:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo="https://www.kernel.org/theme/images/logos/google.png")


def command_pixiv(update, context):
    date_today = datetime.date.today().strftime("%Y%m%d")
    splitted_arguments = parsePixivArgs(update.message.text)

    if "help" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help pixiv"))

    if "query" in update.message.text:
        if "id" in splitted_arguments or splitted_arguments[splitted_arguments.index("query") + 1].isdigit():
            img_id = splitted_arguments[splitted_arguments.index("id") + 1] if "id" in splitted_arguments else splitted_arguments[splitted_arguments.index("query") + 1]
            json_details = pixiv_api.illust_detail(img_id)
            update.message.reply_text(str(json_details.illust))
        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")

    if "ranking" in update.message.text:
        # TODO: not fully implemented
        if "daily" in update.message.text:
            ranking_to_print = ""
            url_list = []
            is_r18 = "r18" in update.message.text
            # Query ranking
            json_ranking = pixiv_api.illust_ranking(mode='day_r18') if is_r18 else pixiv_api.illust_ranking(mode='day')

            for illust in json_ranking.illusts:
                ranking_to_print += str(illust.title + "\n" + illust.image_urls['large'] + "\n")
                url_list.append(illust.image_urls['large'])

            if "pull" in update.message.text:
                update.message.reply_text("pulling today's TOP 30 illustrations, please wait...\n" + "is_r18: " + str(is_r18))
                path_to_save = "img_pixiv/ranking/daily/" + date_today + "/r18/" if is_r18 else "img_pixiv/ranking/daily/" + date_today + "/"
                if not os.path.exists(path_to_save):
                    os.makedirs(path_to_save)
                # Start "pulling" image files.
                for url in url_list:
                    if not os.path.exists(os.path.join(path_to_save, os.path.basename(url))):
                        print("!!!!!!!!!!!!! pulling: " + str(url))
                        pixiv_api.download(url=str(url), path=path_to_save)
                    else:
                        print("!!!!!!!!!!!!! skipping: " + str(url))

                img_files = [f for f in os.listdir(path_to_save) if os.path.isfile(os.path.join(path_to_save, f))]
                for img_file in img_files:
                    img_path = os.path.join(path_to_save, img_file)
                    try:
                        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(img_path, 'rb'))
                        sleep(0.5)
                    except:
                        pass
            else:
                update.message.reply_text("Printing daily TOP 30 illustrations.\nUse pull to download them." + "\n" + ranking_to_print)

        elif "weekly" in update.message.text:
            update.message.reply_text("Not implemented yet!")

        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")

    elif "pull" in update.message.text:
        if "id" in splitted_arguments or splitted_arguments[splitted_arguments.index("pull") + 1].isdigit():
            img_id = splitted_arguments[splitted_arguments.index("id") + 1] if "id" in update.message.text else splitted_arguments[splitted_arguments.index("pull") + 1]
            json_details = pixiv_api.illust_detail(img_id)
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Requested download link is:", json_details.illust.image_urls.large)
            pixiv_api.download(url=json_details.illust.image_urls.large, path="img_pixiv")
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("img_pixiv/" + os.path.basename(json_details.illust.image_urls.large), 'rb'))

        elif "artist-id" in splitted_arguments:
            artist_id = splitted_arguments[splitted_arguments.index("artist-id") + 1]
        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")
    else:
        pass


def process_photo(update, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! PHOTO RECEIVED")
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ID0 IS: ", update.message.photo[0].file_id)

    # Check if the photo is eligible for identifying. If so, process it.
    if update.message.from_user.id in list_user_waiting_identify:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! START IDENTIFYING")
        # DO NOT use reply_text, PhotoMessage does not support it.
        context.bot.send_message(chat_id=update.effective_chat.id, reply_to_message_id=update.message.message_id,
                                 text="Identifying...\n識別中...\nUID: " + str(update.message.from_user.id))
        file = context.bot.get_file(update.message.photo[0].file_id)
        file.download("img_identify/" + update.message.photo[0].file_id)
        list_user_waiting_identify.remove(update.message.from_user.id)

        url_image_to_identify = IMG_SERVER_ADDR + update.message.photo[0].file_id
        cooked_saucenao_url = SAUCENAO_URL + SAUCENAO_API + "&url=" + url_image_to_identify
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Querying URL:", cooked_saucenao_url)

        saucenao_response = requests.get(cooked_saucenao_url)
        saucenao_response.encoding = 'utf-8'
        result = saucenao_response.json()
        if result["header"]["status"] != -2:
            similarity = result['results'][0]['header']['similarity']
            try:
                jp_name = result['results'][0]['data']['jp_name']
            except KeyError:
                jp_name = ""
            try:
                ext_urls = result['results'][0]['data']['ext_urls'][0]
            except KeyError:
                ext_urls = ""
            try:
                pixiv_id = int(result['results'][0]['data']['pixiv_id'])
            except KeyError:
                pixiv_id = ""
            try:
                member_name = result['results'][0]['data']['member_name']
            except KeyError:
                member_name = ""
            try:
                title = result['results'][0]['data']['title']
            except KeyError:
                title = ""
            # There is no need to fetch a thumbnail, Telegram would automatically fetch one on client.
            print_to_user_result = "Similarity " + str(similarity) + '%' + '\n' + "Artist: " + str(
                member_name) + '\n' + "Name: " + str(title) + '' + jp_name + '\n' + "Pixiv id: " + str(
                pixiv_id) + '\n' + "Link: " + '\n' + ext_urls
        try:
            context.bot.send_message(chat_id=update.effective_chat.id, text=print_to_user_result)
        except:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, an error has occurred.")
    else:
        pass


def command_identify(update, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!! IDENTIFY USER ID IS : ", update.message.from_user.id)
    if update.message.from_user.id in list_user_waiting_identify:
        update.message.reply_text("Please wait until current operation is done!")
        return
    update.message.reply_text("Please send an image...\n請發送一張圖片...")
    list_user_waiting_identify.append(update.message.from_user.id)


def command_help(update, context):
    if "pixiv" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help pixiv"))

    if update.message.text.startswith("/help cn"):
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help cn"))

    elif update.message.text.startswith("/help"):
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help"))

    else:
        pass


def parsePixivArgs(str_args):
    splitted_arguments = shlex.split(str_args)
    # Remove first and second command
    splitted_arguments.pop(0)
    return splitted_arguments


# _ Main entry.
def main():
    msg_handler = MessageHandler(Filters.text, process_command)
    dispatcher.add_handler(msg_handler)
    dispatcher.add_handler(MessageHandler(Filters.photo, process_photo))

    # Log into Pixiv.
    pixiv_api.login(PIXIV_USER, PIXIV_PASS)
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
