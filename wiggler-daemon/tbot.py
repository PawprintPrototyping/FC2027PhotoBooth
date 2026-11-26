#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import telegram
from config import CONFIG
from pathlib import Path

from loguru import logger
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from config import CONFIG

MAX_PHOTO_SIZE = (2**20)*10
MAX_VIDEO_SIZE = (2**20)*50

async def send_photo(photo: Path) -> bool:
    if photo.stat().st_size >= MAX_PHOTO_SIZE:
        logger.error(f"Photo size is too big! {photo.stat().st_size} >= {MAX_PHOTO_SIZE}B")
        return False
    bot = telegram.Bot(CONFIG.telegram_api_key)
    async with bot:
        await bot.send_photo(photo=photo, chat_id=CONFIG.channel_id)
    return True


async def send_video(video: Path) -> bool:
    if video.stat().st_size >= MAX_PHOTO_SIZE:
        logger.error(f"Video size is too big! {video.stat().st_size} >= {MAX_VIDEO_SIZE}B")
        return False
    bot = telegram.Bot(CONFIG.telegram_api_key)
    async with bot:
        await bot.send_video(video=video, chat_id=CONFIG.channel_id)
    return True