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
from magic_filter import F

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_tok)
dp = Dispatcher(bot, storage=MemoryStorage())


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
                                    text='Сообщение от id: ' + from_id + ', username: @' + username
                                         + '\n\n' + message.text)
    else:
        await bot.edit_message_text(message_id=predict_post.message_id, chat_id=predict_channel_id,
                                    text='Сообщение от id: ' + from_id + '\n\n' + message.text)


@dp.channel_post_handler(content_types='any')
async def predict_channel(message: types.Message):
    predict_user_id = message.reply_to_message.text.split('id: ')[1].split(',')[0]
    await bot.send_message(chat_id=predict_user_id, text=message.text)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
