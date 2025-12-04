import asyncio
from typing import Iterable, List, Optional

from aiogram.types import user
import pymongo.asynchronous.collection as pymongo_collection
import pymongo.asynchronous.database as pymongo_database
from pymongo.asynchronous.cursor import AsyncCursor

from .models import Link, User, Username


class UserNotExist(Exception):
    pass


class UserDB:
    db: pymongo_database.AsyncDatabase
    collection: pymongo_collection.AsyncCollection = None

    def __init__(self, client):
        self.db = client.get_database("cu_graph_bot")
        self.collection = self.db.get_collection("users")
        asyncio.gather(
            self.collection.create_index("username", unique=True),
            # NOTE: Also temporary
            self.collection.update_many({}, {"$rename": {"_links": "links"}}),
        )

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
        if "links" not in all_friends:
            return []
        links_list = []
        pop_links = []
        for i in all_friends["links"]:
            try:
                links_list.append(Link.model_validate(i))
            except:
                pop_links.append(i["username_to"])
        await self.collection.update_one(
            {"username": username},
            {"$pull": {"links": {"username_to": {"$in": pop_links}}}},
        )
        return links_list

    async def get_user(self, username: Username) -> Optional[User]:
        user_data = await self.collection.find_one({"username": username})
        return User.model_validate(user_data) if user_data is not None else None

    async def get_users(
        self,
        username: Username | Iterable[Username] | None = None,
        links_less_than: Optional[int] = None,
    ) -> AsyncCursor:
        query = {}
        if isinstance(username, (list, tuple)):
            query["$or"] = [{"username": i} for i in username]
        elif username:
            query["username"] = username
        if links_less_than:
            query[f"links.{links_less_than}"] = {"$exists": False}
        all_user_data = self.collection.find(query)
        all_user_data = [User.model_validate(i) async for i in all_user_data]
        return all_user_data

    async def add_link(self, username: Username, link: Link) -> None:
        current_user = await self.collection.find_one({"username": username})
        if current_user is None:
            raise UserNotExist
        for ind, ilink in enumerate(current_user.get("links", [])):
            if ilink["username_to"] == link.username_to:
                await self.collection.update_one(
                    {"username": username},
                    {"$set": {f"links.{ind}.rating": link.rating}},
                )
                return
        else:
            await self.collection.update_one(
                {"username": username}, {"$push": {"links": link.model_dump()}}
            )

    async def count_users(self, links_more_than: int = 4) -> int:
        count = len(
            [
                i
                async for i in self.collection.find(
                    {f"links.{links_more_than}": {"$exists": True}}
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
