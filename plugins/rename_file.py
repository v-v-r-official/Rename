#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import time

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from pyrogram import Client, filters 

from helper_funcs.chat_base import TRChatBase
from helper_funcs.display_progress import progress_for_pyrogram

from pyrogram.errors import UserNotParticipant, UserBannedInChannel 
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image
from database.database import *

async def force_name(bot, message):

    await bot.send_message(
        message.reply_to_message.from_user.id,
        "Enter new name for media\n\nNote : Extension not required",
        reply_to_message_id=message.reply_to_message.message_id,
        reply_markup=ForceReply(True)
    )


@pyrogram.on_message(filters.private & filters.reply & filters.text)
async def cus_name(bot, message):
    if update.from_user.id in Config.BANNED_USERS:
        await update.reply_text("You are B A N N E D")
        return
    TRChatBase(update.from_user.id, update.text, "rename")
    
    if (message.reply_to_message.reply_markup) and isinstance(message.reply_to_message.reply_markup, ForceReply):
        asyncio.create_task(rename_doc(bot, message))     
    else:
        print('No media present')

    
async def rename_doc(bot, message):
    
    mssg = await bot.get_messages(
        message.chat.id,
        message.reply_to_message.message_id
    )    
    
    media = mssg.reply_to_message

    
    if media.empty:
        await message.reply_text('Why did you delete that 😕', True)
        return
        
    filetype = media.document or media.video or media.audio or media.voice or media.video_note
    try:
        actualname = filetype.file_name
        splitit = actualname.split(".")
        extension = (splitit[-1])
    except:
        extension = "mkv"

    await bot.delete_messages(
        chat_id=message.chat.id,
        message_ids=message.reply_to_message.message_id,
        revoke=True
    )
    
    if message.from_user.id not in Config.BANNED_USERS:
        file_name = message.text
        description = script.CUSTOM_CAPTION_UL_FILE.format(newname=file_name)
        download_location = Config.DOWNLOAD_LOCATION + "/"

        sendmsg = await bot.send_message(
            chat_id=message.chat.id,
            text=script.DOWNLOAD_START,
            reply_to_message_id=message.message_id
        )
        
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=media,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(
                script.DOWNLOAD_START,
                sendmsg,
                c_time
            )
        )
        if the_real_download_location is not None:
            try:
                await bot.edit_message_text(
                    text=script.SAVED_RECVD_DOC_FILE,
                    chat_id=message.chat.id,
                    message_id=sendmsg.message_id
                )
            except:
                await sendmsg.delete()
                sendmsg = await message.reply_text(script.SAVED_RECVD_DOC_FILE, quote=True)

            new_file_name = download_location + file_name + "." + extension
            os.rename(the_real_download_location, new_file_name)
            try:
                await bot.edit_message_text(
                    text=script.UPLOAD_START,
                    chat_id=message.chat.id,
                    message_id=sendmsg.message_id
                    )
            except:
                await sendmsg.delete()
                sendmsg = await message.reply_text(script.UPLOAD_START, quote=True)
            # logger.info(the_real_download_location)

            thumb_image_path = download_location + str(message.from_user.id) + ".jpg"
            if not os.path.exists(thumb_image_path):
                mes = await thumb(message.from_user.id)
                if mes != None:
                    m = await bot.get_messages(message.chat.id, mes.msg_id)
                    await m.download(file_name=thumb_image_path)
                    thumb_image_path = thumb_image_path
                else:
                    thumb_image_path = None                    
            else:
                width = 0
                height = 0
                metadata = extractMetadata(createParser(thumb_image_path))
                if metadata.has("width"):
                    width = metadata.get("width")
                if metadata.has("height"):
                    height = metadata.get("height")
                Image.open(thumb_image_path).convert("RGB").save(thumb_image_path)
                img = Image.open(thumb_image_path)
                img.resize((320, height))
                img.save(thumb_image_path, "JPEG")

            c_time = time.time()
            await bot.send_document(
                chat_id=message.chat.id,
                document=new_file_name,
                thumb=thumb_image_path,
                caption=description,
                # reply_markup=reply_markup,
                reply_to_message_id=message.reply_to_message.message_id,
                progress=progress_for_pyrogram,
                progress_args=(
                    script.UPLOAD_START,
                    sendmsg, 
                    c_time
                )
            )

            try:
                os.remove(new_file_name)
            except:
                pass                 
            try:
                os.remove(thumb_image_path)
            except:
                pass  
            try:
                await bot.edit_message_text(
                    text=script.AFTER_SUCCESSFUL_UPLOAD_MSG,
                    chat_id=message.chat.id,
                    message_id=sendmsg.message_id,
                    disable_web_page_preview=True
                )
            except:
                await sendmsg.delete()
                await message.reply_text(script.AFTER_SUCCESSFUL_UPLOAD_MSG, quote=True)
                
    else:
        await bot.send_message(
            chat_id=message.chat.id,
            text="You're B A N N E D",
            reply_to_message_id=message.message_id
        )
    update_channel = Config.UPDATE_CHANNEL
    if update_channel:
        try:
            user = await bot.get_chat_member(update_channel, update.chat.id)
            if user.status == "kicked":
               await update.reply_text(" Sorry, You are **B A N N E D**")
               return
        except UserNotParticipant:
            #await update.reply_text(f"Join @{update_channel} To Use Me")
            await update.reply_text(
                text="**Please Join My Update Channel Before Using Me..**",
                reply_markup=InlineKeyboardMarkup([
                    [ InlineKeyboardButton(text="Join My Updates Channel", url=f"https://t.me/{update_channel}")]
              ])
            )
            return  
        else:
            await bot.send_message(
                chat_id=update.chat.id,
                text=Translation.REPLY_TO_DOC_FOR_RENAME_FILE,
                reply_to_message_id=update.message_id
            )
