import datetime
from time import sleep

from helper import *
import os
import main3
import requests
from state_control import StateControl, GlobalConst


def command_pixiv(update, context, pixiv_api):
    date_today = datetime.date.today().strftime("%Y%m%d")
    args = parsePixivArgs(update.message.text)

    if "help" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help pixiv"))
        return

    if "query" in update.message.text:
        if "id" in args or args[args.index("query") + 1].isdigit():
            img_id = args[args.index("id") + 1] if "id" in args else args[args.index("query") + 1]
            json_details = pixiv_api.illust_detail(img_id)
            update.message.reply_text(str(json_details.illust))
        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")

    if "ranking" in update.message.text:
        # TODO: not fully implemented
        if "daily" in update.message.text:
            ranking_to_print = ""
            url_list = []
            loop_limit = 999
            current_loop = 0
            is_r18 = "r18" in update.message.text
            # Query ranking
            json_ranking = pixiv_api.illust_ranking(mode='day_r18') if is_r18 else pixiv_api.illust_ranking(mode='day')
            if args[args.index("daily") + 1].isdigit():
                loop_limit = int(args[args.index("daily") + 1])

            for illust in json_ranking.illusts:
                if current_loop < loop_limit:
                    current_loop += 1
                    ranking_to_print += str(illust.title + "\n" + illust.image_urls['large'] + "\n")
                    url_list.append(illust.image_urls['large'])
                else:
                    break

            # Check if user wants to pull the images.
            if "pull" in update.message.text:
                update.message.reply_text("Please wait...\n" + "is_r18: " + str(is_r18))
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
                update.message.reply_text("Printing daily ranking illustrations.\nUse pull to download them." + "\n" + ranking_to_print)

        elif "weekly" in update.message.text:
            update.message.reply_text("Not implemented yet!")

        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")

    elif "pull" in update.message.text:
        # Check ID.
        if "id" in args or args[args.index("pull") + 1].isdigit():
            img_id = args[args.index("id") + 1] if "id" in update.message.text else args[args.index("pull") + 1]
            json_details = pixiv_api.illust_detail(img_id)
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Requested download link is:", json_details.illust.image_urls.large)
            pixiv_api.download(url=json_details.illust.image_urls.large, path="img_pixiv")
            context.bot.send_photo(chat_id=update.effective_chat.id, photo=open("img_pixiv/" + os.path.basename(json_details.illust.image_urls.large), 'rb'))

        elif "artist-id" in args:
            artist_id = args[args.index("artist-id") + 1]
        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")
    else:
        pass


def command_identify(update, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!! IDENTIFY USER ID IS : ", update.message.from_user.id)
    if update.message.from_user.id in StateControl.list_user_waiting_identify:
        update.message.reply_text("Please wait until current operation is done!")
        return
    update.message.reply_text("Please send an image...\n請發送一張圖片...")
    StateControl.list_user_waiting_identify.append(update.message.from_user.id)


def command_debug(update, context):
    if "photo" in update.message.text:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo="https://www.kernel.org/theme/images/logos/google.png")


def command_help(update, context):
    if "pixiv" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help pixiv"))
        return

    if update.message.text.startswith("/help cn"):
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help cn"))
        return

    elif update.message.text.startswith("/help"):
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help"))

    else:
        pass


def identify_photo(user_id, file_id, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! START IDENTIFYING")
    file = context.bot.get_file(file_id)
    file.download("img_identify/" + file_id)
    StateControl.list_user_waiting_identify.remove(user_id)

    url_image_to_identify = GlobalConst.IMG_SERVER_ADDR + file_id
    cooked_saucenao_url = GlobalConst.SAUCENAO_URL + GlobalConst.SAUCENAO_API + "&url=" + url_image_to_identify
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!Querying URL:", cooked_saucenao_url)

    try:
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
            parsed_result = "Similarity " + str(similarity) + '%' + '\n' + "Artist: " + str(
                member_name) + '\n' + "Name: " + str(title) + '' + jp_name + '\n' + "Pixiv id: " + str(
                pixiv_id) + '\n' + "Link: " + '\n' + ext_urls
            return parsed_result

    except Exception as ex:
        return "Sorry, an error has occurred. ERR_TRACE:\n" + str(ex)
