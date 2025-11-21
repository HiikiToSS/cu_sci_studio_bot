import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

#AllowedSex = Literal["male", "female"]

def check_tg_username(username: str) -> str:
    pattern = r"^[A-Za-z0-9_]+$"
    if re.match(pattern, username):
        return username
    raise ValueError(f'{username} is not valid username')


class Link(BaseModel):
    username_to: Annotated[str, AfterValidator(check_tg_username)]
    rating: int = Field(ge=1,le=3)

class User(BaseModel) :
    username: Annotated[str, AfterValidator(check_tg_username)]
    # TODO: Add sex, course, etc.
    #sex: AllowedSex
    links: list[Link] = []