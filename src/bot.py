import asyncio
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

load_dotenv()


tkn = os.getenv('TG_BOT_TOKEN')
TOKEN = tkn

users = []

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command('start'))
async def start_handler(message: types.Message):
    await message.answer("Укажи юзернеймы друзей (@username)")

@dp.message(Command('get_names'))
async def get_usS(message: types.Message):
    all_users_and_rating = "\n".join(f"{username} - {rating}" for user in users for username, rating in user.items())
    await message.answer(all_users_and_rating)


def is_valid_username(text: str):
    pattern = r"^@[A-Za-z0-9_]+$"
    return bool(re.match(pattern, text))


@dp.message()
async def user_name_checker(message: types.Message):
    msg = (message.text).strip()

    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Ежедневно", callback_data=f"3:{msg}"),
        InlineKeyboardButton(text="Раз в неск дней", callback_data=f"2:{msg}"),
        InlineKeyboardButton(text="Раз в 2+ недели", callback_data=f"1:{msg}")]
    ])

    if not is_valid_username(msg):
        await message.answer("Напиши юз друга в формате \"@username\"")
    else:
        await message.answer('Насколько часто вы общаетесь?', reply_markup=kb)


@dp.callback_query()
async def process_data(callback: CallbackQuery):
    us, rating = callback.data.split(':')[1], callback.data.split(':')[0]
    users.append({us : rating})
    await callback.message.edit_text(f"Пасибки<3, я записал {us} в тетрадочку",reply_markup=None)
    print(f'Добавил {us} с оценкой {rating}')


async def main():
    await dp.start_polling(bot)