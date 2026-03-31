from aiogram.fsm.state import StatesGroup, State


class SearchStates(StatesGroup):
    waiting_for_query = State()
    waiting_for_city = State()
    waiting_for_min_price = State()
    waiting_for_max_price = State()
