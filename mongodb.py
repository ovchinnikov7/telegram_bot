import os
import certifi

from os.path import dirname, join
from datetime import datetime

import pymongo
from aiogram.types import Message
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from typing import List
from db_types import UserType, AnecdoteType, GameType

ca = certifi.where()
dotenv_path = join(dirname(__file__), './.env')
load_dotenv(dotenv_path)


def create_user(db: Database, message: Message):
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
    }
    inserted = db.users.insert_one(new_user)

    return bool(inserted)


def update_user(db: Database, message: Message):
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
    top_users = [user for user in users.find({"chat_id": message.chat.id}).sort('activity', pymongo.DESCENDING).limit(5)]

    return top_users


def get_random_anecdote(db: Database, message: Message) -> str:
    updated = update_user(db, message)
    anecdotes: Collection[AnecdoteType] = db.anecdotes
    random_anecdote: AnecdoteType = anecdotes.aggregate([{"$sample": {'size': 1}}]).next()
    return random_anecdote.get("text").replace("\\n", "\n")


def create_game(db: Database, message: Message):
    pass
    # games: Collection[User] = db.games
    # game = games.find_one({"id": message.from_user.id, "chat_id": message.chat.id})
    # if games:
    #     return None
    #
    # new_game = {
    #     "id": message.from_user.id,
    #     "results": {
    #
    #     }
    #     "played_at": datetime.now(),
    # }
    # inserted = db.users.insert_one(new_game)
    #
    # return bool(inserted)


def connect() -> MongoClient:
    return MongoClient(
        f'mongodb+srv://{os.environ.get("MONGO_DB_USERNAME")}:{os.environ.get("MONGO_DB_PASSWORD")}@jokerbotcluster'
        f'.vkdv76v.mongodb.net/?retryWrites=true&w=majority',
        tlsCAFile=ca,
    )
