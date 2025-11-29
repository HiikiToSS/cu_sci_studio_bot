from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError
from datetime import datetime

from pydantic import BaseModel      # а на кой ляд нам в принципе BaseModel? - вроде тупо класс же можно создать 

from typing import List, Optional

from dotenv import load_dotenv
import os

load_dotenv()


MONGO_DB_TOKEN = os.getenv('MONGO_DB_TOKEN')


try:
    client = MongoClient(MONGO_DB_TOKEN, serverSelectionTimeoutMS=5000)  # 5 секунд на выбор сервера
    
    # Проверка соединения (важно!)
    client.admin.command("ping")
    print("MongoDB connected successfully")

except ServerSelectionTimeoutError as e:
    print("Ошибка подключения к MongoDB:", e)
    exit(1)




class NewUser(BaseModel):
    user_id: str
    friends: List[str] = []

print(NewUser(user_id='tg-1'))



db = client["finik"]
collection = db["students_connection"]

# индекс по user_id
collection.create_index("user_id", unique=True)

docs = [
    {"user_id": 'tg-1', "friends": ['abc', 'fuckk', 'duck']},
    {"user_id": 'tg-2', "friends": ['pigeon', 'abc', 'ауау']},
    {"user_id": 'tg-3', "friends": ['IIIIIIGAR!', 'lion', 'fefe']},
]

for d in docs:
    try:
        collection.insert_one(d)
        print("Inserted smthg")
    except DuplicateKeyError:
        print("Already exists", d["user_id"])


# ______________ Добавление нового друга __________-

user_to_find = 'tg-2'
friend_to_add = 'qwerty'

current_user = collection.find_one({'user_id': user_to_find})

if friend_to_add in current_user['friends']:
    print('Этого кореша ты уже добавил')     #кидать юзеру мсг, что этот чел уже добавлен
else:
    collection.update_one(
        {"user_id": user_to_find},
        {
            "$push": {'friends': friend_to_add}         # {"$addToSet": {"friends": "uiuiuiuiuiuiuiuASJDVZHSDX"}
        }
    )

    print("Updated", collection.find_one({'user_id': user_to_find}))

# print(f'эта карр френды юзера {user_to_find}: {current_user["friends"]}')


# _____________ создание пользователя как такового ______________
user_to_create = 'tg-13'
# сюда, по идее, можно и нужно впихнуть пайдентик модель, но пока оставлю так, ибо с пайдентиком работал недостаточно, а это прототип за вечер

current_user_to_add = collection.find_one({'user_id': user_to_create})
if not(current_user_to_add):
    collection.insert_one(NewUser(user_id=user_to_create).model_dump())
    print(collection.find_one({'user_id': user_to_create}))
else:
    # pass
    print('по идее тупо ничего')         # мы просто не будем создавать юзера: при каждом /start по идее активация и чисто защита от дебила


# __________ получение всех друзей _________
user_to_find_for_all_friends = 'tg-3'
all_friends = collection.find_one({'user_id': user_to_find_for_all_friends})['friends']
print(*all_friends)


# __________ получение пользователя со всеми потрохами _______
user_to_find_for_info = 'tg-1'
all_user_data = collection.find_one({'user_id': user_to_find_for_info})
print(all_user_data)

# обновление списка друзей
collection.update_one(
    {"user_id": 'tg-1'},
    {"$addToSet": {"friends": "uiuiuiuiuiuiuiuASJDVZHSDX"}}      # корректнее чем set всего списка
)

print("\nПосле обновления user_id=1:", collection.find_one({"user_id": 'tg-1'}))
