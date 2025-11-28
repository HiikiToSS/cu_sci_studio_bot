from abc import ABC, abstractmethod
from typing import Optional

from .models import Link, User, Username

import os
from dotenv import load_dotenv
load_dotenv()

BMONGODB_TOKEN = os.getenv('BMONGODB_TOKEN')



class AbstractUserDB(ABC):
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


class ListUserDB(AbstractUserDB):
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

    def get_links(self, username: Username) -> Optional[list[User]]:
        for i in self._users:
            if i.username == username:
                return i._links
        return None

    def add_link(self, username: Username, link: Link) -> None:
        for i in self._users:
            if i.username == username:
                i.set_link(link)
                break
