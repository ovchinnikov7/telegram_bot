import io
import os
import subprocess
from datetime import datetime
from os.path import dirname, join
from typing import List, Optional

import certifi
import pymongo
from aiogram.bot import Bot
from aiogram.types import Message
from dotenv import load_dotenv
from google.cloud.speech import RecognitionConfig, RecognitionAudio, RecognizeResponse
from pymediainfo import MediaInfo
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from telegram.chataction import ChatAction
from telegram.constants import MAX_MESSAGE_LENGTH

from mongodb_types import UserType, AnecdoteType, GameType

ca = certifi.where()
dotenv_path = join(dirname(__file__), './.env')
load_dotenv(dotenv_path)

# speech_client = SpeechClient()

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


async def voice_to_text(message: Message, bot) -> None:
    reply_message = message.reply_to_message
    if reply_message.voice.duration > MY_NERVES_LIMIT:
        await message.reply(POLITE_RESPONSE)
        return

    chat_id = reply_message.chat.id
    file_name = '%s_%s%s.ogg' % (chat_id, reply_message.from_user.id, reply_message.message_id)
    await download_and_prep(file_name, message, bot)

    transcriptions = transcribe(file_name, message)

    if len(transcriptions) == 0 or transcriptions[0] == '':
        await message.reply('Transcription results are empty. You can try setting language manually by '
                            'replying to the voice message with the language code like ru-RU or en-US'
                            )
        return

    for transcription in transcriptions:
        await message.reply(transcription)


def transcribe(file_name: str, message: Message, lang_code: str = 'ru-RU',
               alternatives: List[str] = ['en-US', 'uk-UA']) -> List[str]:
    media_info = MediaInfo.parse(file_name)
    if len(media_info.audio_tracks) != 1 or not hasattr(media_info.audio_tracks[0], 'sampling_rate'):
        # os.remove(file_name)
        raise ValueError('Failed to detect sample rate')
    actual_duration = round(media_info.audio_tracks[0].duration / 1000)

    sample_rate = media_info.audio_tracks[0].sampling_rate
    encoding = RecognitionConfig.AudioEncoding.OGG_OPUS
    if sample_rate not in SUPPORTED_SAMPLE_RATES:
        message.reply('Your voice message has a sample rate of {} Hz which is not in the list '
                      'of supported sample rates ({}).\n\nI will try to resample it, '
                      'but this may reduce recognition accuracy'
                      .format(sample_rate,
                              ', '.join(str(int(rate / 1000)) + ' kHz' for rate in SUPPORTED_SAMPLE_RATES)
                              ))
        message.answer_chat_action(action=ChatAction.TYPING)
        encoding, file_name, sample_rate = resample(file_name)
    config = RecognitionConfig(
        encoding=encoding,
        sample_rate_hertz=sample_rate,
        enable_automatic_punctuation=True,
        language_code=lang_code,
        alternative_language_codes=alternatives,
    )

    try:
        response = regular_upload(file_name, config)
    except Exception as e:
        print(e)
        os.remove(file_name)
        return ['Failed']

    #     db actions

    # os.remove(file_name)

    message_text = ''
    for result in response.results:
        message_text += result.alternatives[0].transcript + '\n'

    return split_long_message(message_text)


async def download_and_prep(file_name: str, message: Message, bot: Bot) -> None:
    file = await bot.download_file_by_id(message.reply_to_message.voice.file_id, f'./{file_name}')
    return file


def resample(file_name) -> (RecognitionConfig.AudioEncoding, str, int):
    new_file_name = file_name + '.raw'

    cmd = [
        'ffmpeg',
        '-loglevel', 'quiet',
        '-i', file_name,
        '-f', 's16le',
        '-acodec', 'pcm_s16le',
        '-ar', str(RESAMPLE_RATE),
        new_file_name
    ]

    try:
        subprocess.run(args=cmd)
    except Exception as e:
        os.remove(file_name)
        raise e

    return RecognitionConfig.AudioEncoding.LINEAR16, new_file_name, RESAMPLE_RATE


def split_long_message(text: str) -> List[str]:
    length = len(text)
    if length < MAX_MESSAGE_LENGTH:
        return [text]

    results = []
    for i in range(0, length, MAX_MESSAGE_LENGTH):
        results.append(text[i:MAX_MESSAGE_LENGTH])

    return results


def regular_upload(file_name: str, config: RecognitionConfig) -> Optional[RecognizeResponse]:
    with io.open(f'./{file_name}', 'rb') as audio_file:
        content = audio_file.read()
    audio = RecognitionAudio(content=content)
    return audio.content
    # return speech_client.recognize(config=config, audio=audio)
