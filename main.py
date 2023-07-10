import random
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from TokEn import key as TOKEN

# Установка логгера
from states import OurStates
from user_class import User

logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

user_mapping: dict[int, User] = dict()

# Колода карт
cards = [
    '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'
]
suits = ['♥', '♦', '♣', '♠']

markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
markup.add(KeyboardButton("Hit"), KeyboardButton("Stand"))


# Функция для подсчета суммы карт
def calculate_score(hand):
    score = 0
    ace_count = 0
    for card in hand:
        if card[0] == 'A':
            score += 11
            ace_count += 1
        elif card[0] in ['K', 'Q', 'J']:
            score += 10
        else:
            score += int(card[0])
    # Пересчитываем значение Aсe в 1, если нужно
    while score > 21 and ace_count > 0:
        score -= 10
        ace_count -= 1
    return score


@dp.message_handler(commands=['start'], state="*")
async def greetings(message: types.Message):
    user_id = message.from_id

    if user_id not in user_mapping:
        user_mapping[user_id] = User(
            user_id=user_id
        )
    await message.answer(
        text='Привет! Я бот для игры в blackjack. Напиши мне своё имя.'
    )

    await OurStates.enter_name.set()


@dp.message_handler(state=OurStates.enter_name)
async def pregame_instr(message: types.Message):
    user_id = message.from_id
    user_mapping[user_id].name = message.text
    await message.reply(
        f"Привет, {user_mapping[user_id].name}. Добро пожаловать в игру Black Jack! Чтобы начать, введите /play")
    await message.reply('Для начала рекомендую ознакомится с правилами:'
                        'https://www.pokerstars.com/ru/casino/how-to-play/blackjack/rules/')
    await OurStates.playing.set()


# Команда для начала игры
@dp.message_handler(commands=['play'], state=OurStates.playing)
async def start_game(message: types.Message):
    user_id = message.from_id
    user = User(user_id=user_id)
    user_mapping[user_id] = user

    # Создаем новую колоду
    user.deck = [(card, suit) for card in cards for suit in suits]
    # Инициализируем карты игрока и дилера
    user.player_hand = []
    user.dealer_hand = []

    # Раздаем карты игроку и дилеру
    for _ in range(2):
        to_user = random.choice(user.deck)
        to_dealer = random.choice(user.deck)
        user.player_hand.append(to_user)
        user.dealer_hand.append(to_dealer)
        user.deck.remove(to_user)
        user.deck.remove(to_dealer)

    # Отправляем сообщение с картами игрока и одной картой дилера
    player_hand_str = ', '.join([f'{card[0]}{card[1]}' for card in user.player_hand])
    await message.reply(f"Ваши карты: {player_hand_str}. Сумма очков: {calculate_score(user.player_hand)}.")
    await message.reply(f"Карта дилера: {user.dealer_hand[0][0]}{user.dealer_hand[0][1]}.")

    # Если у игрока сразу блэкджек (21 очко), игра завершается
    if calculate_score(user.player_hand) == 21:
        await message.reply("У вас блэкджек! Вы победили!")
        return

    # Игрок может взять еще карту или остановиться
    await message.reply("Выберите действие: /hit - взять карту, /stand - остановиться.",
                        reply_markup=markup)


# Команда для взятия карты
@dp.message_handler(Text(equals="Hit"))
@dp.message_handler(commands=['hit'])
async def hit(message: types.Message):
    user = user_mapping[message.from_id]
    # Получаем текущую колоду и руки игрока и дилера из контекста
    deck = user.deck
    player_hand = user.player_hand
    dealer_hand = user.dealer_hand

    # Добавляем игроку новую карту
    new_card = random.choice(deck)
    player_hand.append(new_card)
    deck.remove(new_card)

    while calculate_score(dealer_hand) < 17:
        new_card = random.choice(deck)
        dealer_hand.append(new_card)
        deck.remove(new_card)

    # Отправляем сообщение с новой картой игрока и суммой очков
    await message.reply(
        f"Вы взяли карту {new_card}. Ваши карты: {', '.join(player_hand)}. Сумма очков: {calculate_score(player_hand)}.")

    # Если у игрока больше 21 очка, он проигрывает
    if calculate_score(player_hand) > 21 and calculate_score(dealer_hand) < calculate_score(player_hand):
        await message.reply("У вас перебор! Вы проиграли!")
    elif calculate_score(player_hand) > 21 and calculate_score(dealer_hand) > calculate_score(player_hand):
        await message.reply('Вы выиграли. У Дилера перебор')

    # Игрок может взять еще карту или остановиться
    await message.reply("Выберите действие: /hit - взять карту, /stand - остановиться.")


# Команда для остановки
@dp.message_handler(Text(equals="Stand"))
@dp.message_handler(commands=['stand'])
async def stand(message: types.Message):
    user = user_mapping[message.from_id]
    # Получаем текущую колоду и руки игрока и дилера из контекста
    deck = user.deck
    player_hand = user.player_hand
    dealer_hand = user.dealer_hand

    # Дилер берет карты, пока его счет меньше 17
    while calculate_score(dealer_hand) < 17:
        new_card = random.choice(deck)
        dealer_hand.append(new_card)
        deck.remove(new_card)

    # Отправляем сообщение с картами дилера и его суммой очков
    await message.reply(f"Карты дилера: {', '.join(dealer_hand)}. Сумма очков: {calculate_score(dealer_hand)}.")

    # Определяем победителя
    player_score = calculate_score(player_hand)
    dealer_score = calculate_score(dealer_hand)
    if player_score > dealer_score:
        await message.reply("Вы победили!")
    elif player_score < dealer_score:
        await message.reply("Вы проиграли!")
    else:
        await message.reply("Ничья!")


if __name__ == '__main__':
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True
    )
