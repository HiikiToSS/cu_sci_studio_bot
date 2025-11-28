from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError
from datetime import datetime

from pydantic import BaseModel      # а на кой ляд нам в принципе BaseModel? - вроде тупо класс же можно создать 

try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)  # 5 секунд на выбор сервера
    
    # Проверка соединения (важно!)
    client.admin.command("ping")
    print("MongoDB connected successfully")

except ServerSelectionTimeoutError as e:
    print("Ошибка подключения к MongoDB:", e)
    exit(1)




class NewUser(BaseModel):
    user_id: str
    friends: list()
    last_added_friend_number: int





db = client["finik"]
collection = db["students_connection"]

# индекс по user_id
collection.create_index("user_id", unique=True)

docs = [
    {"user_id": 'tg-1', "friends": ['abc', 'fuckk', 'duck'], 'last_added_friend_number': 3},
    {"user_id": 'tg-2', "friends": ['pigeon', 'abc', 'female'], 'last_added_friend_number': 3},
    {"user_id": 'tg-3', "friends": ['ivan', 'lion', 'female'], 'last_added_friend_number': 3},
]

# ______________ Добавление нового друга __________-
user_to_find = 'tg-2'
user_to_add = 'myLove'

current_user = collection.find_one({'user_id': user_to_find})

if user_to_add in current_user['friends']:
    print('Этого кореша ты уже добавил')     #кидать юзеру мсг, что этот чел уже добавлен
else:
    last_num = current_user['last_added_friend_number']
    collection.update_one(
        {"user_id": user_to_find},
        {
            "$set": {f'friend {last_num}': user_to_add},
            "$inc": {"last_added_id": 1}      # увеличить на 1
        }
    )

    print("Updated", current_user)



# _____________ создание пользователя как такового ______________
user_to_create = 'tg-13'
# сюда, по идее, можно и нужно впихнуть пайдентик модель, но пока оставлю так, ибо с пайдентиком работал недостаточно, а это прототип за вечер

collection.insert_one(NewUser(user_id=user_to_create))



# __________ получение всех друзей _________
user_to_find_for_all_friends = 'tg-3'
all_friends = collection.find_one(user_to_find_for_all_friends)['friends']
print(*all_friends)


# __________ получение пользователя со всеми потрохами _______
user_to_find_for_info = 'tg-1'
all_user_data = collection.find_one(user_to_find_for_info)
print(all_user_data)

for d in docs:
    try:
        collection.insert_one(d)
        print("Inserted", d)
    except DuplicateKeyError:
        print("Already exists", d["user_id"])

print("\nПоиск по user_id=2:")
doc = collection.find_one({"user_id": 2})
print(doc)

# обновление списка друзей
collection.update_one(
    {"user_id": 1},
    {"$addToSet": {"friends": "added_user"}}      # корректнее чем set всего списка
)

print("\nПосле обновления user_id=1:", collection.find_one({"user_id": 1}))
