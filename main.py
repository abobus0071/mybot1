import logging
import random

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
from aiogram.types import ReplyKeyboardRemove

from buttons import game_callback_data, game_kb, rules_kb, play_kb
from casic import calculate_score, get_shuffled_deck, dealer_and_player_hand, hand_texts, get_card_text
from config import key
from states import OurStates
from user_class import User

# Установка логгера
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=key)
dp = Dispatcher(bot, storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

user_mapping: dict[int, User] = dict()


@dp.message_handler(commands=['start'], state="*")
async def greetings(message: types.Message):
    user_id = message.from_id
    if user_id not in user_mapping:
        user_mapping[user_id] = User(
            user_id=user_id
        )
    with open('photo1689150138.jpeg', 'rb') as photo:
        await bot.send_photo(user_id, photo, caption='Привет! Я бот для игры в blackjack. Напиши мне своё имя.'
                             )

    await OurStates.enter_name.set()


@dp.message_handler(commands=["me"], state="*")
async def profile(message: types.Message):
    if message.from_id not in user_mapping:
        await message.answer("Вы ещё не зарегистрированы. Напишите /start.")
        return
    user = user_mapping[message.from_id]
    await message.answer(f'Ваше имя: {user.name}\n'
                         f'Ваш баланс: ${user.count}\n'
                         f'Кол-во сыгранных / выигранных игр: {user.games}/{user.wins}')


@dp.message_handler(commands=['top10'], state="*")
async def top_10_users(message: types.Message):
    # Получаем список пользователей, сортируем по балансу и выбираем топ 10
    top_users = sorted(user_mapping.values(), key=lambda u: u.count, reverse=True)[:10]

    # Формируем текст для вывода
    text = "Топ 10 пользователей по балансу:\n"
    for i, user in enumerate(top_users, start=1):
        text += f"{i}. {user.name}: ${user.count}\n"

    # Отправляем текст пользователю
    await message.answer(text)


@dp.message_handler(state=OurStates.enter_name)
async def name_entered(message: types.Message):
    user_id = message.from_id
    user = user_mapping[user_id]
    user.name = message.text

    hello_msg = f'Привет, {user_mapping[user_id].name}. Добро пожаловать в игру Black Jack! Для начала рекомендую ознакомится с правилами:'
    await message.reply(hello_msg, reply_markup=rules_kb)
    await message.answer('Если ты готов играть нажимай play', reply_markup=play_kb)

    await OurStates.wait_for_play.set()


@dp.message_handler(commands=['play'], state=OurStates.wait_for_play)
@dp.callback_query_handler(game_callback_data.filter(action="play"), state=OurStates.wait_for_play)
async def start_game(message: types.Message | types.CallbackQuery):
    user = user_mapping[message.from_user.id]

    if isinstance(message, types.CallbackQuery):
        call = message
        await bot.answer_callback_query(call.id)
        await bot.send_message(call.from_user.id,
                               f"Введите ставку на данный момент ваш баланс состовляет ${user.count}")
    else:
        await message.reply(f"Введите ставку, на данный момент ваш баланс состовляет ${user.count}")
    await OurStates.bet.set()


@dp.message_handler(state=OurStates.bet)
async def set_bet(message: types.Message):
    user = user_mapping[message.from_id]

    bet_str = message.text
    if bet_str.isdigit() and int(bet_str) <= user.count:
        user.bet = int(bet_str)
    else:
        with open('714502432ca8252b8a2645b302622f2b.jpg', 'rb') as photo:
            await bot.send_photo(message.from_id, photo,
                                 "Вы думаете вы меня переиграете))). Попробуйте ввести свою ставку еще раз")
            return

    user.count -= user.bet

    # Новая раздача
    user.deck = get_shuffled_deck()
    dealer_and_player_hand(user)

    # Отправляем сообщение с картами игрока и одной картой дилера
    player_hand_str = "\n".join(hand_texts(user.player_hand))
    player_score = calculate_score(user.player_hand)
    dealer_card = get_card_text(user.dealer_hand[0])
    await message.reply(f'💲 ставка — ${user.bet} \n'
                        f'💳 баланс — ${user.count}')
    await message.reply(f"• Ваши карты({player_score} очков): \n"
                        f"{player_hand_str}.\n \n"
                        f"• Карта дилера: \n {dealer_card}.")

    # Если у игрока сразу блэкджек (21 очко), игра завершается
    if player_score == 21:
        with open('chelovechek-veselyy_55399611_orig_.jpeg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption="У вас блэкджек! Вы победили!")
        user.count += 2 * user.bet
        user.wins += 1
        user.games += 1
        await message.answer(
            'Пока вы играли мы создали вам профиль(/me), там вы можете просмотреть всю информацию о себе.')
        await message.reply('Если хотите сыграть еще пишите play', reply_markup=play_kb)
        return
    else:
        # Игрок может взять еще карту или остановиться
        await message.answer("Выберите действие: hit - взять карту, stand - остановиться.",
                             reply_markup=game_kb)
    await OurStates.playing.set()


# Команда для взятия карты
@dp.callback_query_handler(game_callback_data.filter(action="hit"), state=OurStates.playing)
@dp.message_handler(Text(equals="Hit"), state=OurStates.playing)
@dp.message_handler(commands=['hit'], state=OurStates.playing)
async def hit(message: types.Message):
    if isinstance(message, types.CallbackQuery):
        call = message
        message = call.message
        await bot.answer_callback_query(call.id)
        await bot.delete_message(message.chat.id, message.message_id)
        user = user_mapping[call.from_user.id]
    else:
        user = user_mapping[message.from_user.id]
        message = message
    # Получаем текущую колоду и руки игрока и дилера из контекста
    deck = user.deck
    player_hand = user.player_hand
    dealer_hand = user.dealer_hand

    # Добавляем игроку новую карту
    new_card = deck.pop()
    player_hand.append(new_card)

    while calculate_score(dealer_hand) < 17:
        new_card1 = deck.pop()
        dealer_hand.append(new_card1)

    # Отправляем сообщение с новой картой игрока и суммой очков
    player_hand_desc = "\n".join(hand_texts(user.player_hand))

    dealer_hand_desc = "\n".join(hand_texts(user.dealer_hand))

    player_score = calculate_score(player_hand)
    dealer_score = calculate_score(dealer_hand)
    await message.answer(
        f"Вы взяли карту {get_card_text(new_card)}.\n"
        f"• Ваши карты({player_score} очков):\n "
        f"{player_hand_desc}.")

    # Если у игрока больше 21 очка, он проигрывает
    if player_score > 21 and dealer_score < player_score:
        with open('nepobeda.jpg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption="У вас перебор! Вы проиграли!",
                                 reply_markup=ReplyKeyboardRemove())
        user.games += 1
        if user.count <= 0:
            user.count += 10
            await message.answer(
                'К сожалению вы обанкротились, но мы предусмотрели такую ситуацию и перевели вам бесплатные $10. В следующий раз будте аккуратнее')
        await message.answer(
            'Пока вы играли мы создали вам профиль(/me), там вы можете просмотреть всю информацию о себе.')
        await message.answer('Если хотите сыграть еще пишите play',
                             reply_markup=play_kb)
        await OurStates.wait_for_play.set()
    elif 21 < player_score < dealer_score:
        await message.answer(f'• Карта дилера({dealer_score} очков): \n'
                             f' {dealer_hand_desc}.')
        with open('chelovechek-veselyy_55399611_orig_.jpeg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption='Вы выиграли. У Дилера перебор',
                                 reply_markup=ReplyKeyboardRemove())
        user.count += 2 * user.bet
        user.wins += 1
        user.games += 1
        await message.answer(
            'Пока вы играли мы создали вам профиль(/me), там вы можете просмотреть всю информацию о себе.')
        await message.answer('Если хотите сыграть еще пишите play',
                             reply_markup=play_kb)
        await OurStates.wait_for_play.set()
    else:
        # Игрок может взять еще карту или остановиться
        await message.answer("Выберите действие: hit - взять карту, stand - остановиться.", reply_markup=game_kb)


# Команда для остановки
@dp.callback_query_handler(game_callback_data.filter(action="stand"), state=OurStates.playing)
@dp.message_handler(Text(equals="Stand"), state=OurStates.playing)
@dp.message_handler(commands=['stand'], state=OurStates.playing)
async def stand(message: types.Message | types.CallbackQuery):
    if isinstance(message, types.CallbackQuery):
        call = message
        message = call.message
        await bot.answer_callback_query(call.id)
        await bot.delete_message(message.chat.id, message.message_id)
        user = user_mapping[call.from_user.id]
    else:
        user = user_mapping[message.from_user.id]
        message = message

    # Получаем текущую колоду и руки игрока и дилера из контекста
    deck = user.deck
    player_hand = user.player_hand
    dealer_hand = user.dealer_hand

    # Дилер берет карты, пока его счет меньше 17
    while calculate_score(dealer_hand) < 17:
        new_card = random.choice(deck)
        dealer_hand.append(new_card)
        deck.remove(new_card)

    cards_desc = []
    for card in dealer_hand:
        nominal, color = card
        desc = f"{nominal} {color}"
        cards_desc.append(desc)

    # Отправляем сообщение с картами дилера и его суммой очков
    await message.answer(f"Карты дилера: {', '.join(cards_desc)}. Сумма очков: {calculate_score(dealer_hand)}.")

    # Определяем победителя
    player_score = calculate_score(player_hand)
    dealer_score = calculate_score(dealer_hand)

    if player_score > dealer_score:
        with open('chelovechek-veselyy_55399611_orig_.jpeg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption="Вы победили!")
        user.count += 2 * user.bet
        user.wins += 1

    elif player_score < dealer_score < 22:
        with open('nepobeda.jpg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption="Вы проиграли!")
    elif dealer_score > 21:
        with open('chelovechek-veselyy_55399611_orig_.jpeg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption="Вы победили!")
        user.count += 2 * user.bet
        user.wins += 1
    else:
        with open('nepobeda.jpg', 'rb') as photo:
            await bot.send_photo(user.user_id, photo, caption="Ничья!")
        user.count += user.bet
    if user.count == 0:
        user.count += 10
        await message.answer(
            'К сожалению вы обанкротились, но мы предусмотрели такую ситуацию и перевели вам бесплатные $10. В следующий раз будте аккуратнее')
    await message.answer('Пока вы играли мы создали вам профиль(/me), там вы можете просмотреть всю информацию о себе.')
    await message.answer('Если хотите сыграть еще пишите play',
                         reply_markup=play_kb)
    user.games += 1
    await OurStates.wait_for_play.set()


if __name__ == '__main__':
    executor.start_polling(
        dispatcher=dp,
        skip_updates=True
    )
