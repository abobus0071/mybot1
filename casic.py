import random


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


suits = ['♥', '♦', '♣', '♠']
cards = [
    '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'
]


def get_shuffled_deck():
    deck = [(card, suit) for card in cards for suit in suits]
    random.shuffle(deck)
    return deck


def get_card_text(card: tuple[str, str]):
    return f"{card[0]}{card[1]}"


def hand_texts(cards: list):
    return [get_card_text(card) for card in cards]


def dealer_and_player_hand(user):
    # Инициализируем карты игрока и дилера
    user.player_hand = []
    user.dealer_hand = []

    # Раздаем карты игроку и дилеру
    for _ in range(2):
        card_1 = user.deck.pop()
        user.player_hand.append(card_1)

        card_2 = user.deck.pop()
        user.dealer_hand.append(card_2)