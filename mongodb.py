import os
from datetime import datetime
from os.path import dirname, join
from typing import List, Optional

import certifi
import pymongo
from aiogram.types import Message
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from mongodb_types import UserType, AnecdoteType, GameType

ca = certifi.where()
dotenv_path = join(dirname(__file__), './.env')
load_dotenv(dotenv_path)

SUPPORTED_SAMPLE_RATES = [8000, 12000, 16000, 24000, 48000]
RESAMPLE_RATE = 48000
UPLOAD_LIMIT = 58  # everything longer than a minute we have to upload to bucket. More than 58 seconds to be sure
MY_NERVES_LIMIT = 5 * 60  # five minutes is all you get bruh. don't be tellin stories
POLITE_RESPONSE = 'Sorry, but no messages longer than 5 minutes.'


def create_user(db: Database, message: Message) -> Optional[bool]:
    users: Collection[UserType] = db.users
    user = users.find_one({"id": message.from_user.id, "chat_id": message.chat.id})
    if user:
        return None

    new_user = {
        "id": message.from_user.id,
        "username": message.from_user.username,
        "chat_id": message.chat.id,
        "is_bot": message.from_user.is_bot,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "full_name": message.from_user.full_name,
        "created_at": datetime.now(),
        "updated_at": None,
        "points": 0,
        "activity": 0,
    }
    inserted = db.users.insert_one(new_user)

    return bool(inserted)


def update_user(db: Database, message: Message) -> Optional[bool]:
    users: Collection[UserType] = db.users
    updated = users.find_one_and_update(
        {
            "id": message.from_user.id,
            "chat_id": message.chat.id,
        },
        {
            "$inc": {"activity": 1},
            "$set": {"updated_at": datetime.now()}
        }
    )

    return bool(updated)


def get_top_users(db: Database, message: Message) -> List[UserType]:
    users: Collection[UserType] = db.users
    top_users = [user for user in
                 users.find({"chat_id": message.chat.id}).sort('activity', pymongo.DESCENDING).limit(5)]

    return top_users


def get_random_anecdote(db: Database, message: Message) -> Optional[str]:
    updated = update_user(db, message)
    anecdotes: Collection[AnecdoteType] = db.anecdotes
    random_anecdote: AnecdoteType = anecdotes.aggregate([{"$sample": {'size': 1}}]).next()
    return random_anecdote.get("text").replace("\\n", "\n")


def create_game(db: Database, results) -> Optional[bool]:
    games: Collection[GameType] = db.games
    new_game = {
        "results": {**results},
        "played_at": datetime.now(),
    }
    inserted = db.games.insert_one(new_game)
    return bool(inserted)


def connect() -> MongoClient:
    return MongoClient(
        f'mongodb+srv://{os.environ.get("MONGO_DB_USERNAME")}:{os.environ.get("MONGO_DB_PASSWORD")}@jokerbotcluster'
        f'.vkdv76v.mongodb.net/?retryWrites=true&w=majority',
        tlsCAFile=ca,
    )
