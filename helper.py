import shlex
import json


def get_help_msg(helpType:str):
    if helpType == "help":
        return """
```
moe-setu-bot by Plow. Released under the GPLv3 License. 
Comes with ABSOLUTELY NO WARRANTY. All rights reserved. 
    
Usage: /<command> <flags>
Note: '/' is omittable for convenience

Available commands:
 /identify       Identify an image and query for its details.
 /upscale        Upscale an image using waifu2x CuNet model.
 /pixiv          Interact with Pixiv, see also /pixiv help.
 /grab           Grab images from yande.re
 /send           Send document through tg.
 /bash           Run bash command, permission required.
 /get-video      Get video from link.
 /get-sticker    (Reply to message) Get sticker set.
 /set-alias [ALIAS] [ORIGINAL]
     Set alias.
 /get-alias      Get alias.
 /echo           Echo what you have sent.
 /help           Print this help message.
 /help cn        輸出中文幫助訊息。
 
Reply with command:
 create-sticker-set [SET_NAME] [EMOJI] "SET_TITLE"
     Create sticker set.
 add-sticker [PACK_NAME] [EMOJI]
     Add sticker to existing set, alias could be used.
 get-sticker    
     Get all stickers from a set.
 
Reply and mention behaviours:
 reply_to_sticker    Get sticker set.
 reply_to_photo      Identify image.
 ```
    """

    if helpType == "help cn":
        return """
```
moe-setu-bot by Plow. Released under the GPLv3 License. 
Comes with ABSOLUTELY NO WARRANTY. All rights reserved. 
    
使用方法: /<指令> <參數>
提示: '/'為方便起見可以忽略

可用指令:
 /identify       識別圖片並搜尋詳情。
 /upscale        使用waifu2x CuNet放大圖片。
 /pixiv          檢索或下載Pixiv各種資源，詳見/pixiv help。
 /grab           從yande.re下載圖片.
 /send           發送檔案.
 /bash           執行bash指令, 需要授權.
 get-video [LINK]     
                 抓取視訊並發送為tg檔案.
 set-alias [ALIAS] [ORIGINAL]
                 設定alias.
 /get-alias      取得當前alias設定.
 /echo           復讀。
 /help cn        輸出此段幫助訊息。
 
回覆簡訊時的可用指令:
 create-sticker-set [SET_NAME] [EMOJI] "SET_TITLE"
     創建貼圖包.
 add-sticker [PACK_NAME] [EMOJI]
     添加貼圖至貼圖包, 可以使用alias簡稱
 get-sticker    
     取得貼圖檔案歸檔.

回覆簡訊並@提及時:
 回覆的內容是貼圖   取得貼圖檔案歸檔.
 回覆的內容是相片   識別圖片並搜尋詳情.

 ```
    """

    if helpType == "help pixiv":
        return """
```
moe-setu-bot by @Plow. Released under the GPLv3 License. 
Comes with ABSOLUTELY NO WARRANTY. All rights reserved.

/pixiv <sub-command> <args> <flags>

Sub-commands: 
 pull          Download specific resource from pixiv.
   id          Illustration ID
   artist-id   Artist ID
 query         Query for a specific resource.
   id          Illustration ID
 find          Search for specified resource.
 ranking <r18> Get illustrations from Pixiv rankings.
   daily       Daily ranking.
   weekly      Weekly ranking.
   
Examples:
  pixiv ranking pull daily 10 r18
  pixiv pull 81347133
  pixiv find キャル
```            
        """


def parsePixivArgs(str_args):
    splitted_arguments = shlex.split(str_args)
    # Remove first and second command
    splitted_arguments.pop(0)
    return splitted_arguments

def parse_args(str_args):
    splitted_arguments = shlex.split(str_args)
    return splitted_arguments

def get_json_dict():
    try:
        with open("alias.json", 'r') as fp:
            return json.load(fp)
    except:
        return {}
