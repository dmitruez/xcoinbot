from aiogram.fsm.state import StatesGroup, State


class ExchangeStates(StatesGroup):
    SELECT_PAYMENT_METHOD = State()
    SELECT_CURRENCY_PAIR = State()
    SELECT_EXCHANGE = State()
    INPUT_AMOUNT = State()
    INPUT_USER_DATA = State()
    CAPTCHA = State()
    TERMS_AGREEMENT = State()
    CONFIRM_ORDER = State()