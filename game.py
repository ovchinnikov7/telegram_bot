import random
from exceptions import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from randomizer import get_random_results, GAME_ITEMS

WAITING_FOR_START, WAITING_FOR_PLAYER, COMPLETED, FINISHED = range(0, 4)

STATUSES = ['Waiting for start.',
            'Game is running.',
            'Game is finished!',
            'Game is finished!']


class Game:
    def __init__(self, board_size=3):
        self.board_size = board_size
        self.game_going = False
        self.players = dict()
        self.results = dict()
        self.board = None
        self.setup_board()

    def get_board(self):
        return self.board

    def start_game(self):
        if self.game_going:
            raise GameStartedError()
        self.setup_board()
        self.game_going = True

    def end_game(self):
        if not self.game_going:
            return -1
        self.game_going = False
        self.reveal_all()
        return self.results

    def clear(self):
        self.players.clear()
        self.results.clear()

    def reveal_one(self, player_id, player_username, button_id):
        if player_id in self.players:
            return -1
        self.players[player_id] = {"result": GAME_ITEMS[self.results[button_id]], "username": player_username}
        self.board.inline_keyboard[int(button_id / self.board_size)][
            button_id - int(button_id / self.board_size) * self.board_size] = InlineKeyboardButton(
            text=self.results[button_id],
            callback_data=-0
        )

    def reveal_all(self):
        for i in range(0, self.board_size - 1):
            for j in range(0, self.board_size):
                self.board.inline_keyboard[i][j] = InlineKeyboardButton(str(self.results[i + j]), callback_data=-0)

    def setup_board(self):
        self.board = InlineKeyboardMarkup(row_width=self.board_size)
        self.board.add(*[InlineKeyboardButton('❓', callback_data=str(i)) for i in range(0, pow(self.board_size, 2))])
        self.board.row(InlineKeyboardButton('Завершить игру', callback_data=-1))
        for i in range(0, pow(self.board_size, 2)):
            self.results.update({i: get_random_results()})
        self.game_going = False
