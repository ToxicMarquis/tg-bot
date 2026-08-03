from aiogram.fsm.state import State, StatesGroup


class ApplicationForm(StatesGroup):
    address = State()
    phone = State()
    service = State()
    slot = State()
    confirm = State()


class AdminForm(StatesGroup):
    add_slots = State()
