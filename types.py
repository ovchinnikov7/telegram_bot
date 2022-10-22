from typing import TypedDict
from datetime import datetime


class User(TypedDict):
    id: int
    username: str
    chat_id: int
    is_bot: bool
    first_name: str
    last_name: str
    full_name: str
    created_at: datetime
    updated_at: datetime
    points: int


class Game(TypedDict):
    id: int
