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
	UPLOAD_MEDIA = State()
	SELECT_BUTTON_TYPE = State()
	WAITING_BUTTON_CONTENT = State()


class UserStates(StatesGroup):
	USERS = State()
	CHOOSE_USER = State()
	WAITING_QUERY = State()
	WAITING_ID = State()


class ChatStates(StatesGroup):
	LIST = State()
	WAITING_REPLY = State()


class ChannelsStates(StatesGroup):
	CHANNELS = State()
	EDIT_MAIN_CHANNEL = State()
	EDIT_BACKUP_CHANNEL = State()
	ADD_LINK = State()


class WelcomeStates(StatesGroup):
	EDIT_TEXT = State()
	UPLOAD_MEDIA = State()
	SELECT_BUTTON_TYPE = State()
	WAITING_BUTTON_TEXT = State()
	WAITING_BUTTON_URL = State()
	WAITING_BUTTON_CONTENT = State()


class BroadcastStates(StatesGroup):
	WAITING_CONTENT = State()
	SELECT_BUTTON_TYPE = State()
	WAITING_BUTTON_TEXT = State()
	WAITING_BUTTON_URL = State()
	WAITING_BUTTON_CONTENT = State()
	CONFIRM_ADD_ANOTHER = State()
	CONFIRM_BROADCAST = State()