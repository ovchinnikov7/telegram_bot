import os
import requests
import logging
import certifi
import re

from os.path import dirname, join
from bs4 import BeautifulSoup
from pymongo import MongoClient
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import Message, User
from dotenv import load_dotenv
from mongodb import *


ca = certifi.where()
dotenv_path = join(dirname(__file__), './.env')
load_dotenv(dotenv_path)

MONGO_CONNECTION_STRING = f'mongodb+srv://{os.environ.get("MONGO_DB_USERNAME")}:{os.environ.get("MONGO_DB_PASSWORD")}@jokerbotcluster.vkdv76v.mongodb.net/?retryWrites=true&w=majority'
client = MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=ca)
db = client.db

bot = Bot(token=os.environ.get("API_TOKEN"))
dp = Dispatcher(bot)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


@dp.message_handler(commands=['start'])
async def start_joking(message: Message):
    new_user = create_user(db, message)
    if new_user:
        await message.answer(f'Добро пожаловать в клуб, {new_user["username"]}!')


@dp.message_handler(commands=['help'])
async def get_help(message: Message):
    await message.answer('Бог поможет!')


if __name__ == '__main__':
    executor.start_polling(dp)
