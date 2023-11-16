import asyncio
import datetime
import sqlite3
import time

from aiogram import Bot, types
from aiogram.utils import executor, exceptions
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from settings import *
from tokens import *
import logging
from aiogram_media_group import media_group_handler
from aiogram.dispatcher.filters import MediaGroupFilter, state
from typing import List

from magic_filter import F

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_tok)
dp = Dispatcher(bot, storage=MemoryStorage())

connection = sqlite3.connect('forms.db', timeout=10)
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS ban_table
              (user_id TEXT, time TEXT)''')
connection.commit()


async def ban(user_id):
    result = cursor.execute("SELECT * FROM ban_table WHERE user_id = '" + str(user_id) + "'").fetchone()
    if result is None:
        cursor.execute("INSERT INTO ban_table (user_id, time) VALUES('"
                       + str(user_id) + "', '" + str('ban') + "')")
        connection.commit()


async def unban(user_id):
    result = cursor.execute("SELECT * FROM ban_table WHERE user_id = '" + str(user_id) + "'").fetchone()
    if result is not None:
        cursor.execute("DELETE FROM ban_table WHERE user_id='" + str(user_id) + "'")
        connection.commit()


async def check_ban(user_id):
    try:

        result = cursor.execute("SELECT * FROM ban_table WHERE user_id = '" + str(user_id) + "'").fetchone()

        if result is None:
            return True

        else:
            await bot.send_message(chat_id=user_id, text='Вы заблокированы')

    except Exception as e:
        print(e)


@dp.message_handler((F.text == '+ban') & (F.chat.id == admin))
async def predict_channel(message: types.Message):
    try:
        ban_user_id = message.reply_to_message.text.split('#id')[1].split(',')[0]
        await ban(ban_user_id)
        await bot.send_message(chat_id=ban_user_id, text='Вы заблокировны')
    except Exception as e:
        try:
            ban_user_id = message.reply_to_message.caption.split('#id')[1].split(',')[0]
            await ban(ban_user_id)
            await bot.send_message(chat_id=ban_user_id, text='Вы заблокировны')
        except Exception as e:
            await message.answer('Неудача: заблокировать можно ответив на первый элемент или текст в медиа-группе')


@dp.message_handler((F.text == '+unban') & (F.chat.id == admin))
async def predict_channel(message: types.Message):
    try:
        ban_user_id = message.reply_to_message.text.split('#id')[1].split(',')[0]
        await unban(ban_user_id)
        await bot.send_message(chat_id=ban_user_id, text='Вы разблокировны')
    except Exception as e:
        try:
            ban_user_id = message.reply_to_message.caption.split('#id')[1].split(',')[0]
            await unban(ban_user_id)
            await bot.send_message(chat_id=ban_user_id, text='Вы разблокировны')
        except Exception as e:
            await message.answer('Неудача: заблокировать можно ответив на первый элемент или текст в медиа-группе')


@dp.message_handler(MediaGroupFilter(is_media_group=True), F.chat.id == admin, content_types=['any'])
@media_group_handler
async def album_handler(messages: List[types.Message]):
    if await check_ban(messages[0].from_id):
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

        try:
            predict_user_id = messages[0].reply_to_message.text.split('#id')[1].split(',')[0]
            await bot.send_media_group(chat_id=predict_user_id, media=media)
        except Exception as e:
            try:
                predict_user_id = messages[0].reply_to_message.caption.split('#id')[1].split(',')[0]
                await bot.send_media_group(chat_id=predict_user_id, media=media)
            except Exception as e:
                print(e)
                pass


@dp.message_handler(F.chat.id == admin, content_types='any')
async def predict_answer_media(message: types.Message):
    try:
        predict_user_id = message.reply_to_message.text.split('#id')[1].split(',')[0]
        await bot.copy_message(chat_id=predict_user_id, from_chat_id=message.chat.id, message_id=message.message_id)
    except Exception as e:
        try:
            predict_user_id = message.reply_to_message.caption.split('#id')[1].split(',')[0]
            await bot.copy_message(chat_id=predict_user_id, from_chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
            print(e)
            pass


@dp.message_handler(F.chat.type == 'private', commands=['start'])
async def magic_start(message: types.Message):
    if await check_ban(message.from_id):
        await message.answer('Привет! Напиши своё сообщение, мы постараемся ответить на него')


@dp.message_handler(F.chat.type == 'private', content_types='text')
async def forward_predict(message: types.Message, state: FSMContext):
    if await check_ban(message.from_id):
        predict_post = await message.copy_to(chat_id=admin)
        from_id = str(message.from_id)
        if message.from_user.username is not None:
            username = str(message.from_user.username)
            await bot.edit_message_text(message_id=predict_post.message_id, chat_id=admin,
                                        text=message.text
                                             + '\n\n' + 'Сообщение от #id' + from_id + ', username: @' + username,
                                        entities=message.entities, disable_web_page_preview=True)
        else:
            await bot.edit_message_text(message_id=predict_post.message_id, chat_id=admin,
                                        text=message.text
                                             + '\n\n' + 'Сообщение от #id' + from_id,
                                        entities=message.entities, disable_web_page_preview=True)

        conversation_info = await state.get_data()
        if 'last_conversation' not in conversation_info:
                await state.update_data(last_conversation=int(time.time()))
                await message.answer('Спасибо, сообщение передано в редакцию.')
        else:
            if int(time.time()) - conversation_info['last_conversation'] > 86400:
                await state.update_data(last_conversation=int(time.time()))
                await message.answer('Спасибо, сообщение передано в редакцию.')



@dp.message_handler(F.chat.type == 'private', content_types='sticker')
async def forward_predict(message: types.Message):
    if await check_ban(message.from_id):
        await message.answer('Отправка стикеров не поддерживается')


@dp.message_handler(MediaGroupFilter(is_media_group=True), F.chat.type == 'private', content_types=['photo', 'video'])
@media_group_handler
async def album_handler(messages: List[types.Message], state: FSMContext):
    if await check_ban(messages[0].from_id):
        if messages[0].caption is None:
            from_id = str(messages[0].from_id)
            if messages[0].from_user.username is not None:
                username = str(messages[0].from_user.username)
                media = types.MediaGroup()

                for m in messages:
                    if m.video:
                        media.attach_video(m.video.file_id, caption='\n\n' + 'Сообщение от #id'
                                                                    + from_id + ', username: @' + username)
                    if m.photo:
                        media.attach_photo(m.photo[-1].file_id, caption='\n\n' + 'Сообщение от #id'
                                                                        + from_id + ', username: @' + username)

                await bot.send_media_group(chat_id=admin, media=media)

            else:
                media = types.MediaGroup()
                for m in messages:
                    if m.video:
                        media.attach_video(m.video.file_id,
                                           caption='\n\n' + 'Сообщение от #id' + from_id)
                    if m.photo:
                        media.attach_photo(m.photo[-1].file_id,
                                           caption='\n\n' + 'Сообщение от #id' + from_id)

                await bot.send_media_group(chat_id=admin, media=media)

        else:
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
                            media.attach_photo(m.photo[-1].file_id, caption=m.caption,
                                               caption_entities=m.caption_entities)
                        else:
                            media.attach_photo(m.photo[-1].file_id, caption=m.caption)

                    else:
                        media.attach_photo(m.photo[-1].file_id)

            predict_post = await bot.send_media_group(chat_id=admin, media=media)

            from_id = str(messages[0].from_id)

            if messages[0].from_user.username is not None:
                username = str(messages[0].from_user.username)
                await bot.edit_message_caption(message_id=predict_post[0].message_id, chat_id=admin,
                                               caption=messages[0].caption
                                                       + '\n\n' + 'Сообщение от #id' + from_id + ', username: @' + username,
                                               caption_entities=messages[0].caption_entities)
            else:
                await bot.edit_message_caption(message_id=predict_post[0].message_id, chat_id=admin,
                                               caption=messages[0].caption + '\n\n'
                                                       + 'Сообщение от #id' + from_id,
                                               caption_entities=messages[0].caption_entities)

        conversation_info = await state.get_data()
        if 'last_conversation' not in conversation_info:
            await state.update_data(last_conversation=int(time.time()))
            await messages[0].answer('Спасибо, сообщение передано в редакцию.')
        else:
            if int(time.time()) - conversation_info['last_conversation'] > 86400:
                await state.update_data(last_conversation=int(time.time()))
                await messages[0].answer('Спасибо, сообщение передано в редакцию.')


@dp.message_handler(F.chat.type == 'private', content_types=['photo', 'video', 'animation', 'document'])
async def forward_predict_media(message: types.Message, state: FSMContext):
    if await check_ban(message.from_id):
        from_id = str(message.from_id)
        if message.caption is None:
            if message.from_user.username is not None:
                username = str(message.from_user.username)
                await message.copy_to(chat_id=admin,
                                      caption='\n\n' + 'Сообщение от #id' + from_id + ', username: @' + username)
            else:
                await message.copy_to(chat_id=admin, caption='\n\n' + 'Сообщение от #id' + from_id)

        else:
            predict_post = await message.copy_to(chat_id=admin)

            if message.from_user.username is not None:
                username = str(message.from_user.username)
                await bot.edit_message_caption(message_id=predict_post.message_id, chat_id=admin,
                                               caption=message.caption
                                                       + '\n\n' + 'Сообщение от #id' + from_id + ', username: @' + username,
                                               caption_entities=message.caption_entities)
            else:
                await bot.edit_message_caption(message_id=predict_post.message_id, chat_id=admin,
                                               caption=message.caption
                                                       + '\n\n' + 'Сообщение от #id' + from_id,
                                               caption_entities=message.caption_entities)


        conversation_info = await state.get_data()
        if 'last_conversation' not in conversation_info:
            await state.update_data(last_conversation=int(time.time()))
            await message.answer('Спасибо, сообщение передано в редакцию.')
        else:
            if int(time.time()) - conversation_info['last_conversation'] > 86400:
                await state.update_data(last_conversation=int(time.time()))
                await message.answer('Спасибо, сообщение передано в редакцию.')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
