import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field


def check_tg_username(username: str) -> str:
    if username[0] == '@':
        username = username[1:]
    pattern = r"^[A-Za-z0-9_]+$"
    if re.match(pattern, username):
        return username
    raise ValueError(f'{username} is not valid username')

Username = Annotated[str, AfterValidator(check_tg_username), Field(min_length=3)]
#AllowedSex = Literal["male", "female"]

class Link(BaseModel):
    username_to: Username
    rating: int = Field(ge=1,le=3)

class User(BaseModel) :
    username: Username
    # TODO: Add sex, course, etc.
    #sex: AllowedSex
    links: list[Link] = []