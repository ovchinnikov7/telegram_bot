from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

board = InlineKeyboardMarkup(row_width=3)

button = InlineKeyboardButton('❓', callback_data='0')