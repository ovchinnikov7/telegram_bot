import logging
import os

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, filters
from aiogram.utils import executor
from telegram.parsemode import ParseMode

from minigame import Game, PROMPT, GAME_STATUS, PLAYER_STATUS, ALREADY_PICKED_SLOT, GAME_ENDING, GAME_ENDED, \
    RESULT_ANNOUNCEMENTS, END_PHRASE
from mongodb import create_user, create_game, get_top_users, get_random_anecdote, connect
from randomizer import *

client = connect()
db = client.get_database(os.environ.get('MONGO_DB_NAME'))

bot = Bot(token=os.environ.get("API_TOKEN"))
dp = Dispatcher(bot)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

mini_game = Game()


@dp.message_handler(commands=['anecdote'])
async def anecdote(message: types.Message):
    random_anecdote = get_random_anecdote(db, message)
    await message.answer(random_anecdote or 'Ты мне не нравишься 🤬')


@dp.message_handler(filters.Text(contains=['анек'], ignore_case=True))
async def trigger(message: types.Message):
    random_anecdote = get_random_anecdote(db, message)
    await message.answer(random_anecdote or 'Ты мне не нравишься 🤬')


@dp.message_handler(commands=['c'], commands_ignore_caption=False, content_types=types.ContentType.ANY)
async def test(message: types.Message):
    await message.answer(f'TESTING')


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
        f'{emoji:^5}{idx + 1}\\.  @{user["username"]:<} \\- {user["points"]:<20}' for idx, (user, emoji) in
        enumerate(zip(top_users, get_random_emojis())))
    heading = "*Главные любители _сомнительного_ юмора:*"
    await message.answer(f'{heading:^}\n\n{leaderboard}', parse_mode=ParseMode.MARKDOWN_V2)


@dp.message_handler(commands=['leave'])
async def leave(message: types.Message):
    await message.reply('🫠')


@dp.message_handler(commands=['game'])
async def game(message: types.Message):
    mini_game.start_game()
    await message.answer('🫠')
    await message.answer(PROMPT, reply_markup=mini_game.get_board())


@dp.callback_query_handler(lambda c: c.data and c.data not in [*GAME_STATUS, *PLAYER_STATUS])
async def process_picked_slot(callback_query: types.CallbackQuery):
    revealed_slot = mini_game.reveal(callback_query.from_user.id, callback_query.from_user.username,
                                     int(callback_query.data))
    if revealed_slot == ALREADY_PICKED_SLOT:
        await bot.answer_callback_query(callback_query.id, "Одна игра - одна попытка 😉", show_alert=True)
    else:
        await callback_query.message.edit_text(
            text=f'\n{callback_query.message.text}\n@{callback_query.from_user.username} {RESULT_ANNOUNCEMENTS.get(revealed_slot)}',
            reply_markup=mini_game.get_board())


@dp.callback_query_handler(lambda c: c.data and c.data in [*GAME_STATUS, *PLAYER_STATUS])
async def process_game_results(callback_query: types.CallbackQuery):
    if callback_query.data == GAME_ENDING:
        game_results = mini_game.get_results()
        created = create_game(db, game_results)
        game_results_markup = mini_game.end_game()
        await callback_query.message.edit_text(
            text=f'{callback_query.message.text}\n\n{END_PHRASE} @{callback_query.from_user.username}',
            reply_markup=game_results_markup)
    elif callback_query.data == GAME_ENDED:
        await bot.answer_callback_query(callback_query.id, "Эта игра уже окончена!", show_alert=True)


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
