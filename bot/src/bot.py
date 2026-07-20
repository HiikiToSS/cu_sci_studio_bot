import io
import os
import datetime
from typing import List

import qrcode
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.pymongo import PyMongoStorage
from aiogram.methods import SendMessage, send_message
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReactionTypeEmoji,
    ReplyKeyboardMarkup,
)
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.formatting import as_list
from aiogram.utils.payload import decode_payload
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from pymongo import AsyncMongoClient

from . import callbacks, templates
from .models import Link, User, check_tg_username
from .userdb import UserDB

load_dotenv()

TOKEN = os.getenv("TG_BOT_TOKEN")
if TOKEN is None:
    raise Exception("Couldn't find TG_BOT_TOKEN")

MONGODB_HOST = os.getenv("MONGODB_HOST")
READONLY = os.getenv("READONLY_MODE")
if READONLY.lower() != "true":
    READONLY = False
else:
    READONLY = True

client = AsyncMongoClient(MONGODB_HOST)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=PyMongoStorage(client, db_name="cu_graph_bot"))
scheduler = AsyncIOScheduler()


rkb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Мои контакты"), KeyboardButton(text="Тип личности")],
        [
            KeyboardButton(text="Кол-во пользователей"),
            KeyboardButton(text="Реферальная система"),
        ],
    ]
)


class AddingUser(StatesGroup):
    starting = State()
    sex = State()
    course = State()
    living_place = State()


@dp.message(CommandStart())
async def start_handler(
    message: types.Message, command: CommandObject, state: FSMContext
):
    if READONLY:
        await message.answer(
            templates.readonly_message,
        )
        return
    await state.set_state(AddingUser.starting)
    if command.args:
        linked_by = decode_payload(command.args)
        if linked_by != message.from_user.username:
            user = await userdb.get_user(message.from_user.username)
            if user is None:
                await state.update_data(invited_by=linked_by)
                await userdb.add_invited(linked_by, message.from_user.username)
            elif len(user.links) < 5 and user.invited_by is None:
                await userdb.add_invited_by(message.from_user.username, linked_by)
                await userdb.add_invited(linked_by, message.from_user.username)

    await message.answer(
        templates.starting_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Далее", callback_data=callbacks.StartingCallback().pack()
                    )
                ]
            ]
        ),
    )


@dp.callback_query(callbacks.StartingCallback.filter())
async def next_handler(
    query: CallbackQuery, callback_data: callbacks.StartingCallback, state: FSMContext
):
    if await userdb.get_user(query.from_user.username) is not None:
        await explaining_links(query.message)
        return
    await state.set_state(AddingUser.sex)
    await question_sex(query.message, state)


@dp.message(AddingUser.sex)
async def question_sex(message: types.Message, state: FSMContext):
    await state.set_state(AddingUser.course)
    await message.answer(
        "Для начала подскажи, пожалуйста, какого ты пола?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Мужской",
                        callback_data=callbacks.SexCallback(sex="male").pack(),
                    ),
                    InlineKeyboardButton(
                        text="Женский",
                        callback_data=callbacks.SexCallback(sex="female").pack(),
                    ),
                ]
            ]
        ),
    )


@dp.callback_query(callbacks.SexCallback.filter())
async def process_sex(
    query: CallbackQuery, callback_data: callbacks.SexCallback, state: FSMContext
):
    await state.update_data(sex=callback_data.sex)
    await question_course(query.message, state)


@dp.message(AddingUser.course)
async def question_course(message: types.Message, state: FSMContext):
    await state.set_state(AddingUser.living_place)
    await message.answer(
        "На каком курсе учишься?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="1",
                        callback_data=callbacks.CourseCallback(course=1).pack(),
                    ),
                    InlineKeyboardButton(
                        text="2",
                        callback_data=callbacks.CourseCallback(course=2).pack(),
                    ),
                ]
            ]
        ),
    )


@dp.callback_query(callbacks.CourseCallback.filter())
async def process_course(
    query: CallbackQuery, callback_data: callbacks.CourseCallback, state: FSMContext
):
    await state.update_data(course=callback_data.course)
    await question_living(query.message, state)


@dp.message(AddingUser.living_place)
async def question_living(message: types.Message, state: FSMContext):
    await state.set_state(None)
    await message.answer(
        "Где живёшь?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="В Облаке",
                        callback_data=callbacks.LivingCallback(living="Cloud").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="В Космосе",
                        callback_data=callbacks.LivingCallback(living="Cosmos").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="В Байкале",
                        callback_data=callbacks.LivingCallback(living="Baikal").pack(),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="Не в общаге",
                        callback_data=callbacks.LivingCallback(
                            living="Homeless"
                        ).pack(),
                    ),
                ],
            ]
        ),
    )


@dp.callback_query(callbacks.LivingCallback.filter())
async def process_living(
    query: CallbackQuery, callback_data: callbacks.LivingCallback, state: FSMContext
):
    state_data = await state.get_data()
    await userdb.add_user(
        User(
            username=query.from_user.username,
            userid=query.from_user.id,
            chatid=query.message.chat.id,
            sex=state_data["sex"],
            course=state_data["course"],
            living=callback_data.living,
            invited_by=state_data.get("invited_by"),
        )
    )
    await state.clear()
    await explaining_links(query.message)


async def explaining_links(message: types.Message):
    await message.answer(
        templates.explaining_links_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Далее", callback_data=callbacks.TypeInfoCallback().pack()
                    )
                ]
            ]
        ),
    )


@dp.callback_query(callbacks.TypeInfoCallback.filter())
async def start_survey(query: CallbackQuery, callback_data: callbacks.TypeInfoCallback):
    if not READONLY:
        await query.message.answer(
            "Напиши юзернейм (@username) и я предложу тебе выбрать его категорию",
            reply_markup=rkb,
        )


def rating_to_text(rating: int) -> str:
    if rating == 3:
        return "Друг"
    if rating == 2:
        return "Приятель"
    if rating == 1:
        return "Знакомый"
    raise Exception("Rating_to_text получил invalid значение")


@dp.message(F.text[0] == "@")
async def user_name_checker(message: types.Message):
    await userdb.add_ids_to_user(
        message.from_user.username, message.from_user.id, message.chat.id
    )
    msg = (message.text).strip()
    try:
        username_to = check_tg_username(msg)
    except ValueError:
        await message.answer('Напиши юзернейм в формате "@username"')
        return
    if username_to == message.from_user.username:
        await message.react([ReactionTypeEmoji(emoji="🥰")])
        await message.answer(
            "Любовь к себе это, конечно, хорошо, но, пожалуйста, добавь кого-нибудь другого"
        )
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Близкий друг",
                    callback_data=callbacks.LinkCallback(
                        username_to=username_to, rating=3
                    ).pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text="Приятель",
                    callback_data=callbacks.LinkCallback(
                        username_to=username_to, rating=2
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Знакомый",
                    callback_data=callbacks.LinkCallback(
                        username_to=username_to, rating=1
                    ).pack(),
                ),
            ],
        ]
    )

    await message.answer("Кто он для тебя?", reply_markup=kb)


@dp.callback_query(callbacks.LinkCallback.filter())
async def process_data(query: CallbackQuery, callback_data: callbacks.LinkCallback):
    from_username = query.from_user.username
    if await userdb.get_user(from_username) is None:
        await query.message.answer("Похоже тебе нужно перезапустить бота: /start")
        return
    await userdb.add_link(
        from_username,
        Link(username_to=callback_data.username_to, rating=callback_data.rating),
    )
    await query.message.edit_text(
        as_list(
            f"✅ @{callback_data.username_to} добавлен как {rating_to_text(callback_data.rating).lower()}",
            "\n📝 Чтобы добавить ещё друга — просто введи следующий юзернейм.",
            "\n🔁 Чем больше друзей ты добавишь — тем точнее будет твой социальный портрет!",
        ).as_html(),
        reply_markup=None,
    )


@dp.message(F.text == "Мои контакты")
async def get_usS(message: types.Message):
    await userdb.add_ids_to_user(
        message.from_user.username, message.from_user.id, message.chat.id
    )

    links = await userdb.get_links(message.from_user.username)
    if len(links) == 0:
        await message.answer("Ты ещё не добавил связи!\nВведи юзернейм (@username)")
        return

    friends, buddy, familiar = (
        ["• @" + i.username_to for i in filter(lambda x: x.rating == rate, links)]
        for rate in range(3, 0, -1)
    )

    all_users_and_rating = as_list(
        "Друзья:", *friends, "", "Приятели:", *buddy, "", "Знакомые:", *familiar
    ).as_html()
    await message.answer(all_users_and_rating, reply_markup=rkb)


@dp.message(F.text == "Узнать тип личности")
async def redirect_summary(message: types.Message):
    await get_summary(message)


@dp.message(F.text == "Тип личности")
async def get_summary(message: types.Message):
    await userdb.add_ids_to_user(
        message.from_user.username, message.from_user.id, message.chat.id
    )

    links = await userdb.get_links(message.from_user.username)
    ratings = [i.rating for i in links]
    if len(ratings) < 5:
        await message.answer(
            "К сожалению, ты написал слишком мало для полноценного отчёта. Давай постараемся добавить всех друзей!"
        )
    p1 = ratings.count(1) / len(ratings)
    p2 = ratings.count(2) / len(ratings)
    p3 = ratings.count(3) / len(ratings)
    if p3 >= 0.5:
        await message.answer(
            templates.make_type_str(
                "Сердце компании",
                "Вы создаете глубокие, осознанные отношения. Для вас важно не количество контактов, а их качество и надежность",
                [
                    "Умеете выстраивать доверительные отношения",
                    "Создаете ощущение безопасности для близких",
                    "Ваше окружение знает: на вас можно положиться",
                    "Формируете тесные сплоченные группы",
                ],
                'Попробуйте иногда быть "социальным мостом" — знакомить своих друзей из разных кругов. Ваша глубина общения может стать основой для новых интересных компаний',
            ),
        )
    elif p2 >= 0.4:
        await message.answer(
            templates.make_type_str(
                "Социальный организатор",
                "Вы — мастер поддерживать ровные, комфортные отношения. С вами легко и приятно общаться на повседневные темы",
                [
                    "Создаете здоровую атмосферу в коллективе",
                    "Умеете поддерживать стабильные связи",
                    "Легко находите общий язык с разными людьми",
                    "Отлично чувствуете социальные границы",
                ],
                "Попробуйте выбрать 1-2 самых интересных вам приятеля и предложить им более тесное общение — совместный проект или регулярные встречи. Ваши легкие связи могут перерасти в нечто большее",
            ),
        )
    elif p3 >= 0.25 and p2 >= 0.25 and p1 >= 0.25:
        await message.answer(
            templates.make_type_str(
                "Универсальный коннектор",
                "Вы легко перемещаетесь между разными социальными слоями. От тактических знакомств до близкой дружбы — вы чувствуете себя комфортно на любом уровне",
                [
                    "Социальная гибкость и адаптивность",
                    "Видите ценность в разных типах отношений",
                    "Можете быть связующим звеном между группами",
                    "Быстро ориентируетесь в социальном контексте",
                ],
                "Используйте свой дар соединять людей! Организуйте мини-встречи людей из разных ваших кругов — возможно, вы создадите новые интересные коллаборации",
            ),
        )
    elif p3 >= 0.35 and p1 >= 0.25:
        await message.answer(
            templates.make_type_str(
                "Стратегический коммуникатор",
                "Вы сочетаете глубокую эмоциональную привязанность с широким кругом полезных контактов. Это редкий и ценный навык!",
                [
                    "Баланс между глубиной и широтой связей",
                    "Эмоциональная поддержка + практическая польза",
                    "Умеете отделять личное от профессионального",
                    "Создаете разнообразную социальную экосистему",
                ],
                'Подумайте, как ваши "знакомые" могут помочь вашим "друзьям" (и наоборот). Вы идеально positioned для создания синергии между разными частями вашей сети',
            ),
        )
    elif abs(p3 - p2) <= 0.3 and abs(p2 - p1) / len(ratings) <= 0.3:
        await message.answer(
            templates.make_type_str(
                "Стабильный якорь",
                "Вы выстраиваете гармоничную социальную экосистему, где каждому типу отношений находится свое место",
                [
                    "Социальный баланс и стабильность",
                    "Четкое понимание разных уровней общения",
                    "Умение распределять эмоциональные ресурсы",
                    "Предсказуемость и надежность для окружения",
                ],
                'Ваша сила — в стабильности. Подумайте, не хотите ли вы немного "сдвинуть баланс" в какую-то сторону: углубить несколько связей или, наоборот, расширить круг тактических контактов',
            ),
        )
    else:
        await message.answer(
            "Прости, я не знаю какой тип личности у тебя. Ты воистину уникален"
        )


@dp.message(F.text == "Кол-во пользователей")
async def get_count(message: types.Message):
    await userdb.add_ids_to_user(
        message.from_user.username, message.from_user.id, message.chat.id
    )
    count = await userdb.count_users()
    await message.answer(
        f"Ботом уже воспользовались {count} человек{'а' if count % 10 >= 2 and count % 10 < 5 else ''}!\nНапоминаю, что для участия в розыгрыше нужно подписаться на @campusdna"
    )


@dp.message(F.text == "Реферальная система")
async def get_referral(message: types.Message):
    if READONLY:
        await message.answer(templates.readonly_message)
        return

    def generate_message(
        link: str, str_list: List[str] = None, points: int = None
    ) -> str:
        message = (
            "**🚀 Участвуй в турнире с реферальной системой\\!**\n"
            + f"Твоя личная ссылка для приглашений:\n`{link}`\n\\(Нажми чтобы скопировать\\)\n\n"
            + "✨ Каждый приглашённый друг \\= \\+1 к твоим шансам на победу\\!\n"
            + "Главное — чтобы он указал минимум 5 связей\n"
            + "Приглашение засчитывается, если у человека заполнено меньше 5 связей"
        )

        if not message:
            message += "Пока что никто не переходил по ссылке"
        return message

    await userdb.add_ids_to_user(
        message.from_user.username, message.from_user.id, message.chat.id
    )

    main_user = await userdb.get_user(message.from_user.username)
    if len(main_user.links) < 5:
        await message.answer("Для доступа к реферальной программе отметь 5\\+ связей")
        return

    link = await create_start_link(bot, message.from_user.username, encode=True)

    img = qrcode.make(link)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()
    qr_file = BufferedInputFile(img_byte_arr, f"qr_{message.from_user.id}.png")

    if not main_user.invited:
        await message.answer_photo(
            photo=qr_file,
            caption=generate_message(link),
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return
    users = await userdb.get_users(username=main_user.invited)
    str_list = []
    points = 0
    for user in users:
        str_list.append(
            "• @" + user.username + " - " + ("🟡" if len(user.links) < 5 else "🟢")
        )
        if len(user.links) >= 5:
            points += 1

    await message.answer_photo(
        photo=qr_file,
        caption=generate_message(link, str_list, points),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await message.answer(
        "Давай посмотрим, кто перешёл по твоей ссылке\n"
        + "\n".join(str_list)
        + f"\nВсего баллов: {points}"
    )


async def notify_users():
    users = await userdb.get_users(links_less_than=4, chatid=True)
    for user in users:
        try:
            await bot.send_message(
                chat_id=user.chatid, text=templates.notification_message
            )
        except:
            pass


async def main():
    global userdb
    userdb = UserDB(client)
    # scheduler.add_job(notify_users, CronTrigger(hour=22, minute=12))
    # scheduler.add_job(
    #     notify_users,
    #     IntervalTrigger(
    #         days=1,
    #         start_date=datetime.datetime.now() + datetime.timedelta(seconds=5),
    #     ),
    # )
    # scheduler.start()
    await dp.start_polling(bot)
