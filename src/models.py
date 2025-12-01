import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field


def check_tg_username(username: str) -> str:
    username = username.strip().strip('@')
    pattern = r"^[A-z0-9_]+$"
    if re.match(pattern, username):
        return username
    raise ValueError(f'{username} is not valid username')

Username = Annotated[str, AfterValidator(check_tg_username)]
Sex = Literal["male", "female"]
Living = Literal["Cloud", "Cosmos", "Baikal", "Homeless"]

class Link(BaseModel):
    username_to: Username
    rating: int = Field(ge=1,le=3)

class User(BaseModel) :
    username: Username
    # TODO: Add sex, course, etc.
    sex: Sex
    course: int = Field(ge=1,le=2)
    living: Living
    _links: list[Link] = []

    def set_link(self, link: Link):
        for i in self._links:
            if i.username_to == link.username_to:
                i = link
                return
        self._links.append(link)