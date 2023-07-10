__all__ = ['OurStates']

from aiogram.dispatcher.filters.state import State, StatesGroup


class OurStates(StatesGroup):
    enter_name = State()
    playing = State()