import asyncio
import os
from tkinter import W
from typing import Iterable, List, Optional

import pymongo.asynchronous.collection as pymongo_collection
import pymongo.asynchronous.database as pymongo_database
from dotenv import load_dotenv
from pymongo import AsyncMongoClient
from pymongo.asynchronous.cursor import AsyncCursor
from pymongo.errors import ServerSelectionTimeoutError

from .models import Link, User, Username


class UserNotExist(Exception):
    pass


class UserDB:
    db: pymongo_database.AsyncDatabase
    collection: pymongo_collection.AsyncCollection = None

    def __init__(self, client):
        self.db = client.get_database("cu_graph_bot")
        self.collection = self.db.get_collection("users")
        asyncio.create_task(self.collection.create_index("username", unique=True))

    async def add_user(self, user: User) -> None:
        current_user_to_add = await self.collection.find_one(
            {"username": user.username}
        )
        if not (current_user_to_add):
            await self.collection.insert_one(user.model_dump())
        else:
            pass

    async def get_links(self, username: Username) -> List[Link]:
        all_friends = await self.collection.find_one({"username": username})
        if all_friends is None:
            raise UserNotExist
        if "_links" not in all_friends:
            return []
        return [Link.model_validate(i) for i in all_friends["_links"]]

    async def get_user(self, username: Username) -> Optional[dict]:
        all_user_data = await self.collection.find_one({"username": username})
        return all_user_data

    async def get_users(
        self,
        username: Username | Iterable[Username] | None,
        links_less_than: Optional[int],
    ) -> AsyncCursor:
        query = {}
        if username is List:
            query["$or"] = [{"username": i} for i in username]
        elif username:
            query["username"] = username
        if links_less_than:
            query[f"_links.{links_less_than}"] = {"$exists": False}
        all_user_data = self.collection.find(query)
        return all_user_data

    async def add_link(self, username: Username, link: Link) -> None:
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

    async def count_users(self, links_more_than: int = 4) -> int:
        count = len(
            [
                i
                async for i in self.collection.find(
                    {f"_links.{links_more_than}": {"$exists": True}}
                )
            ]
        )
        return count

    # NOTE: This is temporary function for fixing current database
    # And should be deleted someday because of obvious performance loss
    async def add_ids_to_user(
        self, username: Username, userid: int, chatid: int
    ) -> None:
        await self.collection.update_one(
            {"username": username}, {"$set": {"userid": userid, "chatid": chatid}}
        )

    async def add_invited(self, username: Username, username_invited: Username) -> None:
        await self.collection.update_one(
            {"username": username}, {"$addToSet": {"invited": username_invited}}
        )

    async def add_invited_by(
        self, username: Username, username_invited_by: Username
    ) -> None:
        await self.collection.update_one(
            {"username": username}, {"$set": {"invited_by": username_invited_by}}
        )
