from typing import Optional

from .models import Link, User


class UserDB:
    _users: list[User]

    def __init__(self):
        self._users = []
    
    def add_user(self, user: User):
        self._users.append(user)
    
    def get_user(self, username: str) -> Optional[User]:
        for i in self._users:
            if i.username == username:
                return i
        return None

    def get_links(self, username: str) -> list[User]:
        for i in self._users:
            if i.username == username:
                return i.links

    def add_link(self, username: str, link: Link):
        for i in self._users:
            if i.username == username:
                i.links.append(link)
                break