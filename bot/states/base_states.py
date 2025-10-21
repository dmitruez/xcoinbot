from aiogram.fsm.state import StatesGroup, State


# Состояния для FSM
class CaptchaStates(StatesGroup):
        WAITING_CAPTCHA = State()


class UserChatStates(StatesGroup):
        WAITING_MESSAGE = State()
