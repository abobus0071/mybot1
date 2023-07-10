__all__ = ['User']


class User:
    user_id: int
    name: str
    deck: list | None
    player_hand: list | None
    dealer_hand: list | None

    def __init__(self, user_id: int, name: str = None):
        self.user_id = user_id
        self.name = name
        self.deck = None
        self.player_hand = None
        self.dealer_hand = None

