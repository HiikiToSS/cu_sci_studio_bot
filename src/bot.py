import asyncio
import os
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, callback_data
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

from .models import Link, User, Username
from .userdb import UserDB

load_dotenv()

userdb = UserDB()

tkn = os.getenv("TG_BOT_TOKEN")
TOKEN = tkn

bot = Bot(token=TOKEN)
dp = Dispatcher()


class LinkCallback(callback_data.CallbackData, prefix="link"):
    username_to: str
    rating: int


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
    try:
        username_to = Username(msg)
    except ValueError:
        await message.answer('Напиши юз друга в формате "@username"')
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ежедневно",
                    callback_data=LinkCallback(
                        username_to=username_to, rating=3
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Раз в неск дней",
                    callback_data=LinkCallback(
                        username_to=username_to, rating=2
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Раз в 2+ недели",
                    callback_data=LinkCallback(
                        username_to=username_to, rating=1
                    ).pack(),
                ),
            ]
        ]
    )

    await message.answer("Насколько часто вы общаетесь?", reply_markup=kb)


@dp.callback_query(LinkCallback.filter())
async def process_data(query: CallbackQuery, callback_data: LinkCallback):
    if userdb.get_user(query.from_user.username) is None:
        userdb.add_user(User(username=query.from_user.username))
    userdb.add_link(
        query.from_user.username,
        Link(username_to=callback_data.username_to, rating=callback_data.rating),
    )
    await query.message.edit_text(
        f"Пасибки<3, я записал @{Username(callback_data.username_to)} в тетрадочку",
        reply_markup=None,
    )


async def main():
    await dp.start_polling(bot)
