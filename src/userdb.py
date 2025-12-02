import asyncio
import os
from abc import ABC, abstractmethod
from typing import List, Optional

import pymongo.asynchronous.collection as pymongo_collection
import pymongo.asynchronous.database as pymongo_database
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from pymongo.errors import ServerSelectionTimeoutError

from .models import Link, User, Username

load_dotenv()

MONGODB_HOST = os.getenv("MONGODB_HOST")


class UserDB(ABC):
    @abstractmethod
    def add_user(self, user: User) -> None:
        pass

    @abstractmethod
    def get_user(self, username: Username) -> Optional[User]:
        pass

    @abstractmethod
    def get_links(self, username: Username) -> Optional[list[User]]:
        pass

    @abstractmethod
    def add_link(self, username: Username, link: Link) -> None:
        pass


class UserNotExist(Exception):
    pass


class MongoUserDB(UserDB):
    client: Optional[AsyncMongoClient] = None
    db: Optional[pymongo_database.AsyncDatabase] = None
    collection: Optional[pymongo_collection.AsyncCollection] = None

    def __init__(self):
        # Не создаем клиент в __init__, а делаем это лениво
        pass

    async def _ensure_connection(self):
        """Ленивая инициализация подключения к MongoDB"""
        if self.client is None:
            try:
                self.client = AsyncMongoClient(
                    MONGODB_HOST, serverSelectionTimeoutMS=5000
                )
                self.db = self.client.get_database("cu_graph_bot")
                self.collection = self.db.get_collection("users")
                await self.collection.create_index("username", unique=True)
            except ServerSelectionTimeoutError as e:
                print("Ошибка подключения к MongoDB:", e)
                raise e

    async def add_user(self, user: User) -> None:
        await self._ensure_connection()
        current_user_to_add = await self.collection.find_one(
            {"username": user.username}
        )
        if not (current_user_to_add):
            await self.collection.insert_one(user.model_dump())
        else:
            pass

    async def get_links(self, username: Username) -> List[Link]:
        await self._ensure_connection()
        all_friends = await self.collection.find_one({"username": username})
        if all_friends is None:
            raise UserNotExist
        if "_links" not in all_friends:
            return []
        return [Link.model_validate(i) for i in all_friends["_links"]]

    async def get_user(self, username: Username) -> Optional[User]:
        await self._ensure_connection()
        all_user_data = await self.collection.find_one({"username": username})
        return all_user_data

    async def add_link(self, username: Username, link: Link) -> None:
        await self._ensure_connection()
        current_user = await self.collection.find_one({"username": username})
        if current_user is None:
            raise UserNotExist
        for ind, ilink in enumerate(current_user.get("_links", [])):
            if ilink["username_to"] == link.username_to:
                await self.collection.update_one(
                    {"username": username},
                    {"$set": {f"_links.{ind}.rating": link.rating}},
                )
                return
        else:
            await self.collection.update_one(
                {"username": username}, {"$push": {"_links": link.model_dump()}}
            )

    async def count_users(self) -> int:
        await self._ensure_connection()
        count = len(
            [i async for i in self.collection.find({"_links.4": {"$exists": True}})]
        )
        return count


class ListUserDB(UserDB):
    _users: list[User]

    def __init__(self) -> None:
        self._users = []

    def add_user(self, user: User) -> None:
        if user in self._users:
            raise ValueError
        self._users.append(user)

    def get_user(self, username: Username) -> Optional[User]:
        for i in self._users:
            if i.username == username:
                return i
        return None

    def get_links(self, username: Username) -> Optional[list[Link]]:
        for i in self._users:
            if i.username == username:
                return i._links
        return None

    def add_link(self, username: Username, link: Link) -> None:
        for i in self._users:
            if i.username == username:
                i.set_link(link)
                break


userdb = MongoUserDB()
