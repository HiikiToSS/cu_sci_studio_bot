import os
from typing import List

from aiogram import Bot, Dispatcher, F, html, types
from aiogram.enums import ParseMode
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
from aiogram.utils.formatting import Bold, CustomEmoji, Text
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
        [KeyboardButton(text="Мои контакты")],
        [KeyboardButton(text="Узнать тип личности")],
    ]
)

starting_message = """🧬 ДОБРО ПОЖАЛОВАТЬ В CAMPUS DNA!

Мы создаём первую карту социальных связей нашего университета. 
Это исследование научной студии, и каждый участник получит:
• Личный анализ социального типа
• Место на интерактивной карте универа
• Шанс выиграть КРУТЫЕ ПРИЗЫ 🎁

🏆 <b>УСЛОВИЯ УЧАСТИЯ В РОЗЫГРЫШЕ:</b>

1. ✅ <b>Подписаться на канал</b> @campusdna
2. ✅ <b>Отметь минимум 5 друзей</b> и оцени вашу близость
3. ✅ <b>Чем больше друзей отметишь</b> — тем точнее будет твой анализ
4. ✅ <b>После завершения опроса</b> ты автоматически попадаешь во ВСЕ розыгрыши

🎁 ПРИЗОВОЙ ФОНД:
• 20 ПИЦЦ (1 пицца = 1 победитель)
• ИГРУШКИ-МИНЬОНЫ 
• МЕРЧ ОТ ЦУ И ПАРТНЁРОВ

📢 <b>Следи за розыгрышами в канале:</b> @campusdna

🧭 <b>ЧТО ДЕЛАТЬ ДАЛЬШЕ:</b>

Сначала тебе нужно ввести базовые сведения: пол, курс, общежитие.
Затем я попрошу тебя ввести юзернеймы твоих друзей в Telegram 
и оценить вашу близость по шкале от 1 до 3.

Чем больше друзей ты отметишь — тем точнее будет твой 
социальный портрет и тем ценнее твой вклад в исследование!

<i>Готов начать и узнать, кто ты в социальной сети университета?</i>"""

explaining_links_message = """НА КАКИЕ ГРУППЫ МЫ ДЕЛИМ СВЯЗИ?
<b>1 — Друзья</b>
<i>«С ними я провожу больше всего времени»</i>  
Постоянное общение в универе и в мессенджерах. Видимся почти каждый день. Делимся личными новостями, поддерживаем друг друга. 

<b>2 — Приятели</b>  
<i>«Всегда подойду спросить: "Как дела? Как жизнь?"»</i>  
Видимся несколько раз в неделю. Общаемся и про учебу, и про жизнь, иногда затрагиваем личное (но не глубокое). Можем вместе пообедать или поиграть в пин-понг.

<b>3 — Знакомые</b>  
<i>«Мы здороваемся в коридоре»</i> 
Видимся изредка, общение короткое и ситуативное. В основном на учебные/повседневные темы."""


class AddingUser(StatesGroup):
    sex = State()
    course = State()
    living_place = State()


@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await message.answer(starting_message, parse_mode=ParseMode.HTML)
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
        "На каком курсе учишься?",
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
        "Где живёшь?",
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
    await message.answer(explaining_links_message, parse_mode=ParseMode.HTML)
    await message.answer("Напиши юзернейм (@username) и я предложу тебе выбрать его категорию", reply_markup=rkb)


def rating_to_text(rating: int) -> str:
    if rating == 3:
        return "Друг"
    if rating == 2:
        return "Приятель"
    if rating == 1:
        return "Знакомый"
    raise Exception("Rating_to_text получил invalid значение")


@dp.message(F.text == "Мои контакты")
async def get_usS(message: types.Message):
    links = await userdb.get_links(message.from_user.username)
    if len(links) == 0:
        await message.answer("Ты ещё не добавил связи!")
        return
    all_users_and_rating = "\n".join(
        f"@{link.username_to} - {rating_to_text(link.rating)}" for link in links
    )
    await message.answer(all_users_and_rating)


def make_type_str(type: str, profile: str, strong_sides: List[str], recomendation: str):
    return f"""🎯<b>ТИП: «{type}»</b>

📊 Ваш профиль:
<i>{profile}</i>

💪 Ваши сильные стороны:
• {"\n• ".join(strong_sides)}

🌟 Рекомендация:
<i>{recomendation}</i>
"""


@dp.message(F.text == "Узнать тип личности")
async def get_summary(message: types.Message):
    links = await userdb.get_links(message.from_user.username)
    ratings = [i.rating for i in links]
    if len(ratings) < 5:
        await message.answer(
            "К сожалению, ты написал слишком мало для полноценного отчёта. Давай постараемся добавить всех друзей!"
        )
    elif ratings.count(3) / len(ratings) > 0.6:
        await message.answer(
            make_type_str(
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
            parse_mode=ParseMode.HTML,
        )
    elif ratings.count(2) / len(ratings) > 0.5:
        await message.answer(
            make_type_str(
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
            parse_mode=ParseMode.HTML,
        )
    elif (
        ratings.count(3) / len(ratings) > 0.25
        and ratings.count(2) / len(ratings) > 0.25
        and ratings.count(1) / len(ratings) > 0.25
    ):
        await message.answer(
            make_type_str(
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
            parse_mode=ParseMode.HTML,
        )
    elif (
        ratings.count(3) / len(ratings) > 0.4 and ratings.count(1) / len(ratings) > 0.3
    ):
        await message.answer(
            make_type_str(
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
            parse_mode=ParseMode.HTML,
        )
    elif (
        abs(ratings.count(3) - ratings.count(2)) / len(ratings) < 0.2
        and abs(ratings.count(2) - ratings.count(1)) / len(ratings) < 0.2
    ):
        await message.answer(
            make_type_str(
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
            parse_mode=ParseMode.HTML,
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
        await message.answer('Напиши юзернейм в формате "@username"')
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
        await query.answer("Похоже тебе нужно перезапустить бота: /start")
        return
    await userdb.add_link(
        from_username,
        Link(username_to=callback_data.username_to, rating=callback_data.rating),
    )
    await query.message.edit_text(
        **Text(
            f"✅ @{callback_data.username_to} добавлен как {rating_to_text(callback_data.rating).lower()}",
            "\n📝 Чтобы добавить ещё друга — просто введи следующий юзернейм.",
            "\n🔁 Чем больше друзей ты добавишь — тем точнее будет твой социальный портрет!",
        ).as_kwargs(),
        reply_markup=None,
    )
