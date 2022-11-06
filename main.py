import asyncio
import logging
import os

from aiogram import F
from aiogram.client.bot import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.router import Router
from aiogram.filters import Command, Text
from aiogram.types import Message, CallbackQuery
from aiogram.types.bot_command import BotCommand
from telegram.parsemode import ParseMode

from minigame import Game, PROMPT, GAME_STATUS, PLAYER_STATUS, ALREADY_PICKED_SLOT, GAME_ENDING, GAME_ENDED, \
    RESULT_ANNOUNCEMENTS, END_PHRASE
from mongodb import create_user, create_game, get_top_users, get_random_anecdote, connect
from randomizer import *
from yandex import Yandex

client = connect()
db = client.get_database(os.environ.get('MONGO_DB_NAME'))

session = AiohttpSession()
bot = Bot(token=os.environ.get("API_TOKEN"), session=session)
dp = Dispatcher()
router = Router()
dp.include_router(router)

mini_game = Game()
yandex_helper = Yandex()


@router.message(Command(commands=['stt']))
async def stt(message: Message):
    if message.reply_to_message and message.reply_to_message.voice:
        text = yandex_helper.stt(message, bot)
        await message.reply(text)
    else:
        await message.reply('Мне нужно голосовое, чтобы привести его  🤬')


@router.message(Command(commands=['tts']))
async def tts(message: Message):
    if message.reply_to_message and message.reply_to_message.text:
        file_path = yandex_helper.tts(text=message.reply_to_message.text, file_path='./audio_file.ogg')
        print(file_path)
        await message.reply_audio(audio=file_path)
        os.remove(file_path)
    elif message.text is not None:
        file_path = yandex_helper.tts(text=message.text)
        await message.reply_audio(audio=file_path)
        os.remove(file_path)
    else:
        await message.answer('Мне нужно голосовое, чтобы привести его  🤬')


@router.message(Command(commands=['anecdote']))
async def anecdote(message: Message):
    random_anecdote = get_random_anecdote(db, message)
    await message.answer(random_anecdote or 'Ты мне не нравишься 🤬')


@router.message(F.text.lower().contains('анек'))
async def trigger(message: Message):
    random_anecdote = get_random_anecdote(db, message)
    await message.answer(random_anecdote or 'Ты мне не нравишься 🤬')


@router.message(Command(commands=['c']))
async def test(message: Message):
    await message.answer(f'TESTING')


@router.message(Command(commands=['start']))
async def start(message: Message):
    created = create_user(db, message)

    if created:
        await message.reply(f'Добро пожаловать в клуб, @{message.from_user.username}')
    else:
        await message.reply(f'С тобой мы уже знакомы, @{message.from_user.username} 😅')


@router.message(Command(commands=['help']))
async def help(message: Message):
    await message.reply('Ну, я могу анекдот рассказать..?')


@router.message(Command(commands=['top']))
async def top(message: Message):
    top_users = get_top_users(db, message)
    leaderboard = '\n'.join(
        f'{emoji:^5}{idx + 1}\\.  @{user["username"]:<} \\- {user["points"]:<20}' for idx, (user, emoji) in
        enumerate(zip(top_users, get_random_emojis())))
    heading = "*Главные любители _сомнительного_ юмора:*"
    await message.answer(f'{heading:^}\n\n{leaderboard}', parse_mode=ParseMode.MARKDOWN_V2)


@router.message(Command(commands=['leave']))
async def leave(message: Message):
    await message.reply('🫠')


@router.message(Command(commands=['game']))
async def game(message: Message):
    mini_game.start_game()
    await message.answer('🫠')
    await message.answer(PROMPT, reply_markup=mini_game.get_board())


@router.callback_query((~(F.data.in_({*GAME_STATUS, *PLAYER_STATUS}))))
async def process_picked_slot(callback_query: CallbackQuery):
    revealed_slot = mini_game.reveal(callback_query.from_user.id, callback_query.from_user.username,
                                     int(callback_query.data))
    print(callback_query.data)
    if revealed_slot == ALREADY_PICKED_SLOT:
        await callback_query.answer("Одна игра - одна попытка 😉", show_alert=True)
    else:
        await bot.edit_message_text(message_id=callback_query.message.message_id,
                                    chat_id=callback_query.message.chat.id,
                                    text=f'\n{callback_query.message.text}\n@{callback_query.from_user.username} '
                                         f'{RESULT_ANNOUNCEMENTS.get(revealed_slot)}',
                                    reply_markup=callback_query.message.reply_markup)


@router.callback_query(F.data.in_({*GAME_STATUS, *PLAYER_STATUS}))
async def process_game_results(callback_query: CallbackQuery):
    if callback_query.data == GAME_ENDING:
        game_results = mini_game.get_results()
        created = create_game(db, game_results)
        game_results_markup = mini_game.end_game()
        await bot.edit_message_text(message_id=callback_query.message.message_id,
                                    chat_id=callback_query.message.chat.id,
                                    text=f'{callback_query.message.text}\n\n{END_PHRASE} @{callback_query.from_user.username}',
                                    reply_markup=game_results_markup)
    elif callback_query.data == GAME_ENDED:
        await callback_query.answer("Эта игра уже окончена!", show_alert=True)


async def setup_bot_commands():
    bot_commands = [
        BotCommand(command="anecdote", description="Про Вовочку, Штирлица, Петьку и Чапаева 🥸"),
        # BotCommand(command="start", description="Войти в игру 😎"),
        BotCommand(command="game", description="Рубануться 💀"),
        BotCommand(command="tts", description="Озвучить текст"),
        BotCommand(command="stt", description="Преобразовать речь в текст"),
        BotCommand(command="help", description="Запросить помощь 🙏🏻"),
        BotCommand(command="top", description="Узнать настоящих ценителей 💯"),
        BotCommand(command="leave", description="Уйти с позором 🏃‍♀️💨"),
    ]
    await bot.set_my_commands(bot_commands)


async def main():
    await setup_bot_commands()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)
    asyncio.run(main())
