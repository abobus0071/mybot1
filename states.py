__all__ = ['OurStates']

from aiogram.dispatcher.filters.state import State, StatesGroup


class OurStates(StatesGroup):
    enter_name = State()
    wait_for_play = State()
    bet = State()
    playing = State()