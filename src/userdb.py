from abc import ABC, abstractmethod
from typing import Optional, List

from .models import Link, User, Username


from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ServerSelectionTimeoutError

# а на кой ляд нам в принципе BaseModel? - вроде тупо класс же можно создать
from pydantic import BaseModel

import os
from dotenv import load_dotenv
load_dotenv()

MONGO_DB_TOKEN = os.getenv('MONGO_DB_TOKEN')

try:
    client = MongoClient(MONGO_DB_TOKEN, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("MongoDB connected successfully")

except ServerSelectionTimeoutError as e:
    print("Ошибка подключения к MongoDB:", e)
    exit(1)


class NewUser(BaseModel):
    user_id: str
    friends: List[str] = []


db = client["finik"]
collection = db["students_connection"]


class UserAlreadyExistsError(Exception):
    pass


class MongoUserDB():
    # я правда думал запихнуть как-то запихнуть класс и подключение монго тоже сюда: вроде так лучше, но я не уверен как делать инит, так что и ладно

    def add_new_user(self, new_username: User):
        current_user_to_add = collection.find_one({'user_id': new_username})
        if not (current_user_to_add):
            collection.insert_one(NewUser(user_id=new_username).model_dump())
            print(collection.find_one({'user_id': new_username}))
        else:
            pass


    def get_all_friends(self, username: Username):
        all_friends = collection.find_one({'user_id': username})['friends']
        return all_friends


    def get_user(self, username: Username):
        all_user_data = collection.find_one({'user_id': username})
        return all_user_data


    def add_friend(self, username: Username, friend_to_add: Link):
        current_user = collection.find_one({'user_id': username})
        if friend_to_add in current_user['friends']:
            raise UserAlreadyExistsError(f'Друг {friend_to_add} уже добавлен')
        else:
            collection.update_one(
                {"user_id": username},
                {
                    "$push": {'friends': friend_to_add}
                }
            )


# class ListUserDB(UserDB):
#     _users: list[User]

#     def __init__(self) -> None:
#         self._users = []

#     def add_user(self, user: User) -> None:
#         if user in self._users:
#             raise ValueError
#         self._users.append(user)

#     def get_user(self, username: Username) -> Optional[User]:
#         for i in self._users:
#             if i.username == username:
#                 return i
#         return None

#     def get_links(self, username: Username) -> Optional[list[User]]:
#         for i in self._users:
#             if i.username == username:
#                 return i._links
#         return None

#     def add_link(self, username: Username, link: Link) -> None:
#         for i in self._users:
#             if i.username == username:
#                 i.set_link(link)
#                 break
