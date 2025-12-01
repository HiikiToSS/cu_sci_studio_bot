import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    user,
)
from aiogram.utils.formatting import Bold, Text
from dotenv import load_dotenv

from .models import Link, User, check_tg_username
from .userdb import userdb

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
if TOKEN is None:
    raise Exception("Couldn't find TG_BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


class LinkCallback(callback_data.CallbackData, prefix="link"):
    username_to: str
    rating: int


class SexCallback(callback_data.CallbackData, prefix="sex"):
    sex: str


class CourseCallback(callback_data.CallbackData, prefix="course"):
    course: int


class LivingCallback(callback_data.CallbackData, prefix="living"):
    living: str


rkb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Скинь ссылки")],
        [KeyboardButton(text="Посмотреть отчёт")],
    ]
)


class AddingUser(StatesGroup):
    sex = State()
    course = State()
    living_place = State()


@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer("Привет!\nЗдесь должно быть вступительное сообщение о боте")
    if await userdb.get_user(message.from_user.username) is not None:
        await start_survey(message)
        return
    await state.set_state(AddingUser.sex)
    await question_sex(message, state)


@dp.message(AddingUser.sex)
async def question_sex(message: types.Message, state: FSMContext):
    await state.set_state(AddingUser.course)
    await message.answer(
        "Для начала подскажи, пожалуйста, какого ты пола?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Мужской", callback_data=SexCallback(sex="male").pack()
                    ),
                    InlineKeyboardButton(
                        text="Женский", callback_data=SexCallback(sex="female").pack()
                    ),
                ]
            ]
        ),
    )


@dp.callback_query(SexCallback.filter())
async def process_sex(
    query: CallbackQuery, callback_data: SexCallback, state: FSMContext
):
    await state.update_data(sex=callback_data.sex)
    await question_course(query.message, state)


@dp.message(AddingUser.course)
async def question_course(message: types.Message, state: FSMContext):
    await state.set_state(AddingUser.living_place)
    await message.answer(
        "На каком курсе учишься",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="1", callback_data=CourseCallback(course=1).pack()
                    ),
                    InlineKeyboardButton(
                        text="2", callback_data=CourseCallback(course=2).pack()
                    ),
                ]
            ]
        ),
    )


@dp.callback_query(CourseCallback.filter())
async def process_course(
    query: CallbackQuery, callback_data: CourseCallback, state: FSMContext
):
    await state.update_data(course=callback_data.course)
    await question_living(query.message, state)


@dp.message(AddingUser.living_place)
async def question_living(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer(
        "Где живёшь",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="В Облаке",
                        callback_data=LivingCallback(living="Cloud").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="В Космосе",
                        callback_data=LivingCallback(living="Cosmos").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="В Байкале",
                        callback_data=LivingCallback(living="Baikal").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Не в общаге",
                        callback_data=LivingCallback(living="Homeless").pack(),
                    ),
                ],
            ]
        ),
    )


@dp.callback_query(LivingCallback.filter())
async def process_living(
    query: CallbackQuery, callback_data: LivingCallback, state: FSMContext
):
    state_data = await state.get_data()
    await userdb.add_user(
        User(
            username=query.from_user.username,
            sex=state_data["sex"],
            course=state_data["course"],
            living=callback_data.living,
        )
    )
    await start_survey(query.message)


async def start_survey(message: types.Message):
    await message.answer("Укажи юзернеймы друзей (@username)", reply_markup=rkb)


def rating_to_text(rating: int) -> str:
    if rating == 3:
        return "Друг"
    if rating == 2:
        return "Приятель"
    if rating == 1:
        return "Знакомый"
    raise Exception("Rating_to_text получил invalid значение")


@dp.message(F.text == "Скинь ссылки")
async def get_usS(message: types.Message):
    links = await userdb.get_links(message.from_user.username)
    all_users_and_rating = "\n".join(
        f"@{link.username_to} - {rating_to_text(link.rating)}" for link in links
    )
    await message.answer(all_users_and_rating)


@dp.message(F.text == "Посмотреть отчёт")
async def get_summary(message: types.Message):
    links = await userdb.get_links(message.from_user.username)
    ratings = [i.rating for i in links]
    if len(ratings) < 5:
        await message.answer(
            "К сожалению, ты написал слишком мало для полноценного отчёта. Давай постараемся добавить всех друзей!"
        )
    elif ratings.count(3) / len(ratings) > 0.9:
        await message.answer(
            **Text(
                "Ты — '",
                Bold("Абсолютное ядро"),
                "'!\nТы находишься в самом сердце сплочённой группы! Ваш круг - это крепкое братство/сестринство, где все друг с другом на одной волне. Вы команда, которая всегда вместе",
            ).as_kwargs()
        )
    elif (
        ratings.count(3) / len(ratings) > 0.3 and ratings.count(1) / len(ratings) > 0.3
    ):
        await message.answer(
            **Text(
                "Ты — '",
                Bold("Мост между группами"),
                "'!\nТвое общение не ограничено одним кругом. У тебя есть ближний круг ('банда'), надежные приятели и полезные знакомства в разных сферах. Ты умеешь соединять людей.",
            ).as_kwargs()
        )
    elif ratings.count(3) / len(ratings) > 0.5:
        await message.answer(
            **Text(
                "Ты — '",
                Bold("Сердце коллектива"),
                "'!\nВокруг тебя есть небольшое, но очень надежное ядро самых близких людей, а остальные - ваше стабильное и комфортное окружение. Ценишь глубину отношений.",
            ).as_kwargs()
        )
    elif ratings.count(2) / len(ratings) > 0.5:
        await message.answer(
            **Text(
                "Ты — '",
                Bold("Социальный организатор"),
                "'!\nУ тебя нет резких предпочтений, ты со всеми в ровных, добрых и стабильных отношениях. Ты - тот, кто поддерживает здоровую атмосферу в большой компании.",
            ).as_kwargs()
        )
    else:
        await message.answer(
            "Прости, я не знаю какой тип личности у тебя. Ты воистину уникален"
        )


@dp.message(F.text[0] == "@")
async def user_name_checker(message: types.Message):
    msg = (message.text).strip()
    try:
        username_to = check_tg_username(msg)
    except ValueError:
        await message.answer('Напиши юз в формате "@username"')
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Близкий друг",
                    callback_data=LinkCallback(
                        username_to=username_to, rating=3
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Приятель",
                    callback_data=LinkCallback(
                        username_to=username_to, rating=2
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Знакомый",
                    callback_data=LinkCallback(
                        username_to=username_to, rating=1
                    ).pack(),
                ),
            ],
        ]
    )

    await message.answer("Кто он для тебя?", reply_markup=kb)


@dp.callback_query(LinkCallback.filter())
async def process_data(query: CallbackQuery, callback_data: LinkCallback):
    from_username = query.from_user.username
    if from_username is None:
        raise Exception("WTF?")
    if await userdb.get_user(from_username) is None:
        await userdb.add_user(User(username=from_username))
    await userdb.add_link(
        from_username,
        Link(username_to=callback_data.username_to, rating=callback_data.rating),
    )
    await query.message.edit_text(
        f"Пасибки<3, я записал @{callback_data.username_to} в тетрадочку",
        reply_markup=None,
    )
