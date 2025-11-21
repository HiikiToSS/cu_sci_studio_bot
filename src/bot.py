import asyncio
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

from .models import Link, User, check_tg_username
from .userdb import UserDB

load_dotenv()

userdb = UserDB()

tkn = os.getenv("TG_BOT_TOKEN")
TOKEN = tkn

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Укажи юзернеймы друзей (@username)")


@dp.message(Command("get_names"))
async def get_usS(message: types.Message):
    links = userdb.get_links(message.from_user.username)
    all_users_and_rating = "\n".join(
        f"{link.username_to} - {link.rating}" for link in links
    )
    await message.answer(all_users_and_rating)


@dp.message()
async def user_name_checker(message: types.Message):
    msg = (message.text).strip()
    if msg[0] == '@':
        msg = msg[1:]
    try:
        check_tg_username(msg)
    except Exception:
        await message.answer('Напиши юз друга в формате "@username"')
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ежедневно", callback_data=f"3:{msg}"),
                InlineKeyboardButton(text="Раз в неск дней", callback_data=f"2:{msg}"),
                InlineKeyboardButton(text="Раз в 2+ недели", callback_data=f"1:{msg}"),
            ]
        ]
    )

    await message.answer("Насколько часто вы общаетесь?", reply_markup=kb)

@dp.callback_query()
async def process_data(callback: CallbackQuery):
    us, rating = callback.data.split(":")[1], callback.data.split(":")[0]
    if userdb.get_user(callback.from_user.username) is None:
        userdb.add_user(User(username=callback.from_user.username))
    userdb.add_link(callback.from_user.username, Link(username_to=us, rating=rating))
    await callback.message.edit_text(
        f"Пасибки<3, я записал {us} в тетрадочку", reply_markup=None
    )
    print(f"Добавил {us} с оценкой {rating}")


async def main():
    await dp.start_polling(bot)
