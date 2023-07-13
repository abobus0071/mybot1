from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData

markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
markup.add(KeyboardButton("Hit"), KeyboardButton("Stand"))

game_callback_data = CallbackData("game", "action")
game_kb = InlineKeyboardMarkup(row_width=2)
hit_bt = InlineKeyboardButton("Hit", callback_data=game_callback_data.new(action="hit"))
stand_bt = InlineKeyboardButton("Stand", callback_data=game_callback_data.new(action="stand"))
game_kb.add(hit_bt, stand_bt)

rules_bt = InlineKeyboardButton("Правила", url='https://www.pokerstars.com/ru/casino/how-to-play/blackjack/rules/')
rules_kb = InlineKeyboardMarkup()
rules_kb.add(rules_bt)

play_bt = InlineKeyboardButton("Play", callback_data=game_callback_data.new(action="play"))
play_kb = InlineKeyboardMarkup(row_width=1)
play_kb.add(play_bt)
