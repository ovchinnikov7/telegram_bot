import os
import logging

from telegram import ParseMode
from randomizer import *
from mongodb import create_user, update_user, get_top_users, connect
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, filters
from aiogram.utils import executor
from game import Game

client = connect()
db = client.get_database(os.environ.get('MONGO_DB_NAME'))

bot = Bot(token=os.environ.get("API_TOKEN"))
dp = Dispatcher(bot)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

game_instance = Game()


@dp.message_handler(filters.Text(contains=['анек'], ignore_case=True))
async def trigger(message: types.Message):
    updated = update_user(db, message)
    await message.answer(f'Ты мне не нравишься 🤬')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    created = create_user(db, message)

    if created:
        await message.reply(f'Добро пожаловать в клуб, @{message.from_user.username}')
    else:
        await message.reply(f'С тобой мы уже знакомы, @{message.from_user.username} 😅')


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.reply('Ну, я могу анекдот рассказать..?')


@dp.message_handler(commands=['top'])
async def top(message: types.Message):
    top_users = get_top_users(db, message)
    leaderboard = '\n'.join(
        f'{emoji:^5}{idx + 1:^5}\\. @{user["username"]:<} \\- {user["points"]:<20}' for idx, (user, emoji) in
        enumerate(zip(top_users, get_random_emojis())))
    heading = "*Главные любители _сомнительного_ юмора*"
    await message.answer(f'{heading:^}\n\n{leaderboard}', parse_mode=ParseMode.MARKDOWN_V2)


@dp.message_handler(commands=['leave'])
async def leave(message: types.Message):
    await message.reply('🫠')


@dp.message_handler(commands=['game'])
async def game(message: types.Message):
    game_instance.start_game()
    await message.answer('🫡')
    await message.answer('Угадайте, где лежит печенье 🍪 и постарайтесь не наткнуться на бомбу 💣',
                         reply_markup=game_instance.get_board())


@dp.callback_query_handler(lambda c: c.data and c.data != '-1')
async def process_game(callback_query: types.CallbackQuery):
    revealed = game_instance.reveal_one(int(callback_query.from_user.id), callback_query.from_user.username,
                                        int(callback_query.data))
    if revealed == -1:
        await bot.answer_callback_query(callback_query.id, "Другим дай поиграть, негодяй!", show_alert=True)
    else:
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            callback_query.inline_message_id, reply_markup=game_instance.get_board())


@dp.callback_query_handler(lambda c: c.data == '-1')
async def finish_game(callback_query: types.CallbackQuery):
    results = game_instance.end_game()
    if results == -1:
        await bot.answer_callback_query(callback_query.id, "Игра уже окончена.", show_alert=True)
    else:
        # create_game(db, results)
        game_instance.clear()
    await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                        callback_query.inline_message_id, reply_markup=game_instance.get_board())


async def setup_bot_commands(disp):
    bot_commands = [
        types.BotCommand("anecdote", "Про Вовочку, Штирлица, Петьку и Чапаева 🥸"),
        types.BotCommand("start", "Войти в игру 😎"),
        types.BotCommand("game", "Рубануться 💀"),
        types.BotCommand("help", "Запросить помощь 🙏🏻"),
        types.BotCommand("top", "Узнать настоящих ценителей 💯"),
        types.BotCommand("leave", "Уйти с позором 🏃‍♀️💨"),

    ]
    await disp.bot.set_my_commands(bot_commands)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=setup_bot_commands)
