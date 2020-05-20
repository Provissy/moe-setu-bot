import shlex


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
 /pixiv          Query or download Pixiv resources, see also /pixiv help.
 /echo           Echo what you have sent.
 /help           Print this help message.
 /help cn        輸出中文幫助訊息。
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
 /echo           復讀。
 /help cn        輸出此段幫助訊息。
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
 ranking <r18> Get illustrations from Pixiv rankings.
   daily       Daily ranking.
   weekly      Weekly ranking.
```
        """


def parsePixivArgs(str_args):
    splitted_arguments = shlex.split(str_args)
    # Remove first and second command
    splitted_arguments.pop(0)
    return splitted_arguments
