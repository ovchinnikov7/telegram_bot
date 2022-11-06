import random

from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

PROMPT = 'Угадайте, где лежит печенье 🍪 и постарайтесь не наткнуться на бомбу 💣'
GAME_STATUS = [GAME_ENDING, GAME_ENDED] = ['ENDING', 'ENDED']
PLAYER_STATUS = [ALREADY_PICKED_SLOT] = ['ALREADY_PICKED_SLOT']
UNKNOWN_SLOT = '❓'
SLOTS = [EMPTY_SLOT, BOMB_SLOT, COOKIE_SLOT, FORTUNE_COOKIE_SLOT] = ['💨', '💣', '🍪', '🥠']
PHRASES = [
    'не нашёл ничего интересного',
    'подорвался на бомбе',
    'нашёл печенье',
    'нашёл печенье с предсказанием',
]
END_PHRASE = 'Игра окончена по инициативе'
RESULT_ANNOUNCEMENTS = {slot: f'{slot} {phrase}' for slot, phrase in zip(SLOTS, PHRASES)}


def get_random_slot_result(i):
    random_int = random.randint(i, 100)
    if random_int < 40:
        return EMPTY_SLOT
    elif random_int < 60:
        return COOKIE_SLOT
    elif random_int < 90:
        return BOMB_SLOT
    else:
        return FORTUNE_COOKIE_SLOT


class Game:
    def __init__(self, board_size=3):
        self.board_size = board_size
        self.slots_count = pow(board_size, 2)
        self.game_going = False
        self.players_results = dict()
        self.answers = list()
        self.visual_board = None

    def get_board(self):
        return self.visual_board

    def get_results(self):
        return self.players_results

    def start_game(self):
        self.setup_board()
        self.game_going = True

    def reveal(self, player_id, player_username, button_id):
        if str(player_id) in self.players_results:
            return ALREADY_PICKED_SLOT
        slot_result = self.answers[button_id]
        self.players_results.update({str(player_id): {"username": player_username, "result": slot_result}})
        print(self.players_results)
        return slot_result

    def setup_board(self):
        self.answers = [get_random_slot_result(i) for i in range(self.slots_count)]
        self.visual_board = InlineKeyboardBuilder().row(
            *[InlineKeyboardButton(text=UNKNOWN_SLOT, callback_data=i) for i in range(self.slots_count)],
            width=self.board_size).row(InlineKeyboardButton(text='Завершить игру', callback_data=GAME_ENDING),
                                       width=1).as_markup()

    def end_game(self):
        if not self.game_going:
            return GAME_ENDED
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.visual_board.inline_keyboard[i][j] = InlineKeyboardButton(text=self.answers[i + j],
                                                                               callback_data=GAME_ENDED)
        self.visual_board.inline_keyboard[-1][-1] = InlineKeyboardButton(text='Завершить игру',
                                                                         callback_data=GAME_ENDED)
        self.answers.clear()
        self.players_results.clear()
        self.game_going = False
        return self.visual_board
