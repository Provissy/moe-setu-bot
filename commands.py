import datetime
import shutil
import subprocess
from time import sleep

from helper import *
import os
import main
import requests
from state_control import StateControl, GlobalConst, APIS
import pixivpy3
import telegram
import traceback
import re


def command_pixiv(update, context, pixiv_api):
    date_today = datetime.date.today().strftime("%Y%m%d")
    args = parsePixivArgs(update.message.text)

    if "help" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help pixiv"))
        return

    # QUERY command to query specified resource.
    if "query" in update.message.text:
        if "id" in args or args[args.index("query") + 1].isdigit():
            img_id = args[args.index("id") + 1] if "id" in args else args[args.index("query") + 1]
            json_details = pixiv_api.illust_detail(img_id)
            update.message.reply_text(str(json_details.illust))
        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")

    # _ RANKING command to interact with pixiv rankings.
    if "ranking" in update.message.text:
        # TODO: not fully implemented
        if "daily" in update.message.text:
            ranking_to_print = ""
            url_list = []
            pixiv_url_list = []
            title_list = []
            current_loop = 0
            is_r18 = "r18" in update.message.text

            # Query ranking
            json_ranking = pixiv_api.illust_ranking(mode='day_r18') if is_r18 else pixiv_api.illust_ranking(mode='day')
            loop_limit = len(json_ranking.illusts)

            if args[args.index("daily") + 1].isdigit():
                loop_limit = int(args[args.index("daily") + 1])

            for illust in json_ranking.illusts:
                if current_loop < loop_limit:
                    current_loop += 1
                    ranking_to_print += str(illust.title + "\n" + illust.image_urls['large'] + "\n")
                    url_list.append(illust.image_urls['large'])
                    pixiv_url_list.append("https://pixiv.net/artworks/" + str(illust.id))
                    title_list.append(illust.title)
                else:
                    break

            # Check if user wants to pull the images.
            if "pull" in update.message.text:
                update.message.reply_text("Please wait...\n" + "is_r18: " + str(is_r18) + "\nDate is: " + date_today)
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
                for index, img_file in enumerate(img_files):
                    img_path = os.path.join(path_to_save, img_file)
                    try:
                        context.bot.send_photo(chat_id=update.effective_chat.id,
                                               caption=title_list[index] + "\n" + pixiv_url_list[index],
                                               photo=open(img_path, 'rb'))
                        sleep(0.5)
                    except:
                        pass
            else:
                update.message.reply_text("Printing daily ranking illustrations.\nUse pull to download them." + "\n" + ranking_to_print)

        elif "weekly" in update.message.text:
            update.message.reply_text("Not implemented yet!")

        else:
            update.message.reply_text("Sorry, wrong usage, see /pixiv help")

    # _ PULL command to download specified resource.
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

    # _ FIND command
    elif "find" in update.message.text:
        key_word = args[args.index("find") + 1]
        json_result = pixiv_api.search_illust(key_word)
        url_list = []
        title_list = []
        pixiv_url_list = []

        for illust in json_result.illusts[:5]:
            url_list.append(illust.image_urls.large)
            title_list.append(illust.title)
            pixiv_url_list.append("https://pixiv.net/artworks/" + str(illust.id))
            context.bot.send_photo(chat_id=update.effective_chat.id,
                                   photo=illust.image_urls.medium,
                                   caption=illust.title + "\n" + "https://pixiv.net/artworks/" + str(illust.id),
                                   )

    elif "init" in update.message.text:
        update.message.reply_text("Re-initialising pixiv api...")
        APIS.pixiv_api = None
        APIS.pixiv_api = pixivpy3.AppPixivAPI()
        APIS.pixiv_api.login(GlobalConst.PIXIV_USER, GlobalConst.PIXIV_PASS)
        update.message.reply_text("Successfully re-initialised pixiv api.")

    # DO NOTHING
    else:
        pass


def command_identify(update, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!! IDENTIFY USER ID IS : ", update.message.from_user.id)
    if update.message   .from_user.id in StateControl.list_user_waiting_identify:
        update.message.reply_text("Please wait until current operation is done!")
        return
    update.message.reply_text("Please send an image...\n請發送一張圖片...")
    StateControl.list_user_waiting_identify.append(update.message.from_user.id)


def command_bash(update, context):
    print("!!!!!!!!!!!!!!!!!!!!bash requeted uid is : " + str(update.message.from_user.id))
    if str(update.message.from_user.id) not in GlobalConst.PRIV_USR:
        update.message.reply_text("Permission denied!")
        return
    pwd = os.popen("pwd").read()
    bash_command = update.message.text[5:]
    bash_output = subprocess.run(bash_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    update.message.reply_text(bash_output.stdout.decode('utf-8'))


def command_grab(update, context):
    try:
        update.message.reply_text("Currently supports yande.re tags only\n當前只支援yande.re標籤檢索\n\nPlease wait...")
        bash_command = "ruby danbooru-ruby-grabber/danbooru.rb -b yandere -f url -l posts=10 " + update.message.text[5:]
        bash_output = subprocess.run(bash_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        update.message.reply_text(bash_output.stdout.decode('utf-8'))

        # Done downloading, start sending.
        image_path = update.message.text[5:]
        img_files = [f for f in os.listdir(image_path) if os.path.isfile(os.path.join(image_path, f))]
        for index, img_file in enumerate(img_files):
            img_path = os.path.join(image_path, img_file)
            try:
                context.bot.send_photo(chat_id=update.effective_chat.id,
                                       caption=img_file,
                                       photo=open(img_path, 'rb'))
                sleep(0.5)
            except:
                pass

        update.message.reply_text("Done grabbing, purging cache...")
        shutil.rmtree(image_path)

    except Exception as e:
        update.message.reply_text(str(e))

def command_get_video(update, context):
    try:
        filename_to_save = os.path.basename(update.message.text[10:]) + ".mp4"
        bash_command = "./youtube-dl -o \"" + filename_to_save + "\" " + update.message.text[10:]
        bash_output = subprocess.run(bash_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        # update.message.reply_text(bash_output.stdout.decode('utf-8'))
        context.bot.send_document(chat_id=update.effective_chat.id,
                                  reply_to_message_id=update.message.message_id,
                                  document= open(filename_to_save, 'rb'))
    except Exception as e:
        update.message.reply_text("Sorry, error occurred:\n" + str(e))


def command_send(update, context):
    if "config.ini" in update.message.text:
        update.message.reply_text("Permission denied")
        return
    context.bot.send_document(chat_id=update.effective_chat.id,
                              reply_to_message_id=update.message.message_id,
                              document= open(update.message.text[5:], 'rb'))


def command_debug(update, context):
    if "photo" in update.message.text:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo="https://www.kernel.org/theme/images/logos/google.png")


def command_help(update, context):
    if "pixiv" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help pixiv"))
        return

    if "cn" in update.message.text:
        update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help cn"))
        return

    update.message.reply_text(parse_mode="MarkdownV2", text=get_help_msg("help"))


def identify_photo(queued, user_id, file_id, context):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! START IDENTIFYING")
    try:
        if queued:
            StateControl.list_user_waiting_identify.remove(user_id)
        file = context.bot.get_file(file_id)
        file.download("img_identify/" + file_id)

        url_image_to_identify = GlobalConst.IMG_SERVER_ADDR + file_id
        cooked_saucenao_url = GlobalConst.SAUCENAO_URL + GlobalConst.SAUCENAO_API + "&url=" + url_image_to_identify
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
            parsed_result = "Similarity " + str(similarity) + '%' + '\n' + "Artist: " + str(
                member_name) + '\n' + "Name: " + str(title) + '' + jp_name + '\n' + "Pixiv id: " + str(
                pixiv_id) + '\n' + "Link: " + '\n' + ext_urls
            return parsed_result

    except Exception as ex:
        return "Sorry, an error has occurred. ERR_TRACE:\n" + str(ex)


def get_stickers(update, context):
    sticker_set = context.bot.get_sticker_set(name=update.message.reply_to_message.sticker.set_name)
    update.message.reply_text("This operation might take some time, please wait\n此項作業可能需時較長, 請稍後\n\n" +
                              "Name: " + sticker_set.name + "\n" +
                              "Title: " + sticker_set.title + "\n" +
                              "Amount: " + str(len(sticker_set.stickers)))
    path_to_save = "img_sticker/" + sticker_set.name + "/"
    os.makedirs(path_to_save, exist_ok=True)
    current_index = 0
    for sticker in sticker_set.stickers:
        try:
            context.bot.get_file(sticker.file_id).download(path_to_save + sticker.set_name + str(current_index) +
                                                      sticker.emoji + ".webp")
            current_index += 1
        except:
            pass

    # Recipe for shrank png
    subprocess.run("mogrify -resize 50% -format png " + path_to_save + "*.webp", shell=True)
    # pack and send
    subprocess.run("tar -cvf " + path_to_save + sticker_set.name + "_webp.tar " + \
                   path_to_save + "*.webp", shell=True)
    subprocess.run("tar -cvf " + path_to_save + sticker_set.name + "_50%_png.tar " + \
                   path_to_save + "*.png", shell=True)
    context.bot.send_document(chat_id=update.effective_chat.id,
                              reply_to_message_id=update.message.message_id,
                              document=open(path_to_save + sticker_set.name + "_webp.tar", 'rb'))
    context.bot.send_document(chat_id=update.effective_chat.id,
                              reply_to_message_id=update.message.message_id,
                              document=open(path_to_save + sticker_set.name + "_50%_png.tar", 'rb'))


def create_sticker_set(update, context):
    try:
        sticker_type = "document" if hasattr(update.message.reply_to_message.document, 'file_id') else "photo"
        parsed_args = parse_args(update.message.text)
        sticker_set_name = parsed_args[1] + "_by_moe_setu_bot"
        emoji_name = parsed_args[2]
        sticker_set_title = re.findall(r'["](.+?)["]', update.message.text)[0]
        sticker_file_id = update.message.reply_to_message.document.file_id if sticker_type is "document" else \
            update.message.reply_to_message.photo[0].file_id

        if sticker_type is "photo":
            # a photo needs to be converted to tg styled png
            os.makedirs("img_sticker_manager", exist_ok=True)
            context.bot.get_file(sticker_file_id).download("img_sticker_manager/" + sticker_file_id)
            subprocess.run("convert -background none -resize 512x512 img_sticker_manager/" + sticker_file_id +
                            " img_sticker_manager/" + sticker_file_id + ".png" , shell=True)
            sticker_file_path = "img_sticker_manager/" + sticker_file_id + ".png"
            if context.bot.create_new_sticker_set(user_id=update.message.from_user.id,
                                                  name=sticker_set_name,
                                                  title=sticker_set_title,
                                                  emojis=emoji_name,
                                                  png_sticker=open(sticker_file_path, 'rb'),
                                                 ):
                update.message.reply_text("Success! You new sticker set is at:\n" +
                                          "https://t.me/addstickers/" + sticker_set_name)

        elif sticker_type is "document":
            if context.bot.create_new_sticker_set(user_id=update.message.from_user.id,
                                       name=sticker_set_name,
                                       title=sticker_set_name,
                                       emojis=emoji_name,
                                       png_sticker=open(sticker_file_id),
                                       ):
                update.message.reply_text("Success! You new sticker set is at:\n" + "https://t.me/addstickers/" + sticker_set_name + "_by_moe_setu_bot")
    except Exception as e :
        update.message.reply_text(str(e)+"\n"+"create-sticker-set [SET_NAME] [EMOJI] \"SET_TITLE\"")

def add_sticker(update, context):
    try:
        if hasattr(update.message.reply_to_message.document, 'file_id'):
            sticker_type = "document"
            sticker_file_id = update.message.reply_to_message.document.file_id
        elif len(update.message.reply_to_message.photo) is not 0:
            sticker_type = "photo"
            sticker_file_id = update.message.reply_to_message.photo[0].file_id
        elif hasattr(update.message.reply_to_message.sticker, 'file_id'):
            sticker_type = "sticker"
            sticker_file_id = update.message.reply_to_message.sticker.file_id
        else:
            update.message.reply_text("Wrong document type!")
            return

        parsed_args = parse_args(update.message.text)
        sticker_set_name =  parsed_args[1] if parsed_args[1] not in GlobalConst.STICKER_ALIAS else\
            GlobalConst.STICKER_ALIAS[parsed_args[1]]
        emoji_name = parsed_args[2]
        print("!!!!!!!!!!! type is : ", sticker_type)

        if sticker_type is "photo" or "sticker":
            # a photo needs to be converted to tg styled png
            os.makedirs("img_sticker_manager", exist_ok=True)
            context.bot.get_file(sticker_file_id).download("img_sticker_manager/" + sticker_file_id)
            subprocess.run("convert -background none -resize 512x512 img_sticker_manager/" + sticker_file_id +
                            " img_sticker_manager/" + sticker_file_id + ".png" , shell=True)
            sticker_file_path = "img_sticker_manager/" + sticker_file_id + ".png"
            context.bot.add_sticker_to_set(user_id=update.message.from_user.id,
                                              name=sticker_set_name,
                                              emojis=emoji_name,
                                              png_sticker=open(sticker_file_path, 'rb'))

        elif sticker_type is "document":
            context.bot.add_sticker_to_set(user_id=update.message.from_user.id,
                                              name=sticker_set_name,
                                              emojis=emoji_name,
                                              png_sticker=sticker_file_id)

        update.message.reply_text("Successfully added one sticker to:\n" + "https://t.me/addstickers/" + sticker_set_name)

    except Exception as e :
        update.message.reply_text(str(e) + "\n" + traceback.format_exc())


def command_set_alias(update, context):
    parsed_args = parse_args(update.message.text)
    GlobalConst.STICKER_ALIAS[parsed_args[1]] = parsed_args[2]
    with open('alias.json', 'w') as fp:
        json.dump(GlobalConst.STICKER_ALIAS, fp)


def command_get_alias(update, context):
    update.message.reply_text(str(GlobalConst.STICKER_ALIAS))
