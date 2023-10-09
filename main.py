import asyncio
import datetime
import sqlite3
from aiogram import Bot, types
from aiogram.utils import executor, exceptions
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from settings import *
from tokens import *
import logging
from aiogram_media_group import media_group_handler
from aiogram.dispatcher.filters import MediaGroupFilter
from typing import List

from magic_filter import F

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_tok)
dp = Dispatcher(bot, storage=MemoryStorage())


@dp.channel_post_handler(content_types='any')
async def predict_channel(message: types.Message):
    try:
        predict_user_id = message.reply_to_message.text.split('id: ')[1].split(',')[0]
        await bot.send_message(chat_id=predict_user_id, text=message.text)
    except Exception as e:
        try:
            predict_user_id = message.reply_to_message.caption.split('id: ')[1].split(',')[0]
            await bot.send_message(chat_id=predict_user_id, text=message.text)
        except Exception as e:
            await message.answer('Сообщение не орправлено: Ответить можно на первый элемент или текст в медиа-группе')


@dp.message_handler(commands=['start'])
async def magic_start(message: types.Message):
    await message.answer('Привет')


@dp.message_handler(content_types='text')
async def forward_predict(message: types.Message):
    predict_post = await message.copy_to(chat_id=predict_channel_id)
    from_id = str(message.from_id)
    if message.from_user.username is not None:
        username = str(message.from_user.username)
        await bot.edit_message_text(message_id=predict_post.message_id, chat_id=predict_channel_id,
                                    text=message.text
                                         + '\n\n' + 'Сообщение от id: ' + from_id + ', username: @' + username,
                                    entities=message.entities, disable_web_page_preview=True)
    else:
        await bot.edit_message_text(message_id=predict_post.message_id, chat_id=predict_channel_id,
                                    text=message.text
                                         + '\n\n' + 'Сообщение от id: ' + from_id,
                                    entities=message.entities, disable_web_page_preview=True)


@dp.message_handler(MediaGroupFilter(is_media_group=True), content_types=['photo', 'video'])
@media_group_handler
async def album_handler(messages: List[types.Message]):
    media = types.MediaGroup()
    for m in messages:
        if m.video:
            if m.caption:
                if m.caption_entities:
                    media.attach_video(m.video.file_id, caption=m.caption, caption_entities=m.caption_entities)
                else:
                    media.attach_video(m.video.file_id, caption=m.caption)
            else:
                media.attach_video(m.video.file_id)
        if m.photo:
            if m.caption:
                if m.caption_entities:
                    media.attach_photo(m.photo[-1].file_id, caption=m.caption, caption_entities=m.caption_entities)
                else:
                    media.attach_photo(m.photo[-1].file_id, caption=m.caption)

            else:
                media.attach_photo(m.photo[-1].file_id)

    predict_post = await bot.send_media_group(chat_id=predict_channel_id, media=media)

    from_id = str(messages[0].from_id)
    if messages[0].from_user.username is not None:
        username = str(messages[0].from_user.username)
        print(messages[0].caption_entities)
        await bot.edit_message_caption(message_id=predict_post[0].message_id, chat_id=predict_channel_id,
                                       caption=messages[0].caption
                                               + '\n\n' + 'Сообщение от id: ' + from_id + ', username: @' + username,
                                       caption_entities=messages[0].caption_entities)
    else:
        await bot.edit_message_caption(message_id=predict_post[0].message_id, chat_id=predict_channel_id,
                                       caption=messages[0].caption + '\n\n'
                                               + 'Сообщение от id: ' + from_id,
                                       caption_entities=messages[0].caption_entities)


@dp.message_handler(content_types=['photo', 'video', 'animation', 'document'])
async def forward_predict_media(message: types.Message):
    predict_post = await message.copy_to(chat_id=predict_channel_id)
    from_id = str(message.from_id)
    if message.from_user.username is not None:
        username = str(message.from_user.username)
        await bot.edit_message_caption(message_id=predict_post.message_id, chat_id=predict_channel_id,
                                       caption=message.caption
                                               + '\n\n' + 'Сообщение от id: ' + from_id + ', username: @' + username,
                                       caption_entities=message.caption_entities)
    else:
        await bot.edit_message_caption(message_id=predict_post.message_id, chat_id=predict_channel_id,
                                       caption=message.caption
                                               + '\n\n' + 'Сообщение от id: ' + from_id + '\n\n' + message.caption,
                                       caption_entities=message.caption_entities)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
