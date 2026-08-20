from aiogram.fsm.state import State, StatesGroup


class AppealForm(StatesGroup):
    category = State()
    full_name = State()
    phone = State()
    question = State()
