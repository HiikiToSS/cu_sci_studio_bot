import re
from typing import Annotated, Literal, Optional

from pydantic import AfterValidator, BaseModel, Field


def check_tg_username(username: str) -> str:
    username = username.strip().strip("@")
    pattern = r"^[A-z0-9_]+$"
    if re.match(pattern, username):
        return username
    raise ValueError(f"{username} is not valid username")


Username = Annotated[str, AfterValidator(check_tg_username)]
Sex = Literal["male", "female"]
Living = Literal["Cloud", "Cosmos", "Baikal", "Homeless"]


class Link(BaseModel):
    username_to: Username
    rating: int = Field(ge=1, le=3)


class User(BaseModel):
    userid: int
    chatid: int

    username: Username

    sex: Sex
    course: int = Field(ge=1, le=2)
    living: Living

    _links: list[Link] = []

    invited: list[Username] = []
    invited_by: Optional[Username] = None
