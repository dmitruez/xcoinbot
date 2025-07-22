from aiogram.fsm.state import StatesGroup, State


# Состояния для FSM
class StatsStates(StatesGroup):
	WAITING_START_DATE = State()
	WAITING_END_DATE = State()


class NotificationStates(StatesGroup):
	NOTIFICATION = State()
	EDIT_TEXT = State()
	WAITING_BUTTON_TEXT = State()
	WAITING_BUTTON_URL = State()
	EDITING_BUTTON = State()


class UserStates(StatesGroup):
	USERS = State()
	CHOOSE_USER = State()
	WAITING_QUERY = State()
	WAITING_ID = State()



class ChannelsStates(StatesGroup):
	CHANNELS = State()
	EDIT_MAIN_CHANNEL = State()
	EDIT_BACKUP_CHANNEL = State()
	ADD_LINK = State()
