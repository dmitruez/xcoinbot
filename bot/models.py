# Модели данных

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple
from .utils.work_with_date import get_datetime_now


@dataclass
class User:
	user_id: int
	username: Optional[str]
	full_name: str
	is_active: bool = True
	is_banned: bool = False
	captcha_passed: bool = False
	should_notify: bool = True  # Получать уведомления о смене канала
	join_date: datetime = get_datetime_now()
	banned_when: datetime = None


@dataclass
class Channel:
	channel_id: int
	title: str
	username: Optional[str]
	link: Optional[str] = None
	is_main: bool = False
	is_backup: bool = False


@dataclass
class Admin:
	user_id: int
	username: Optional[str]
	full_name: str
	level: int = 1  # Уровень доступа (1 - базовый, 2 - полный)


@dataclass
class Captcha:
	user_id: int
	text: str
	attempts: int = 0  # При трех не правильных попытках банить вход на 5 мин
	created_at: datetime = get_datetime_now()


@dataclass
class Button:
	id: str
	text: str
	button_type: str
	value: str


@dataclass
class MessageTemplate:
	"""Модель шаблона уведомления о смене канала"""
	text: str
	media_type: str | None
	media_id: str | None
	buttons: List[Button]
	
	def has_buttons(self) -> bool:
		return len(self.buttons) > 0


@dataclass
class BroadcastMessage:
	text: str
	media_type: str | None
	media_id: str | None
	buttons: List[Button]
	sent_at: datetime
	sent_by: int
	success_count: int = 0
	error_count: int = 0
	total_users: int = 0
	id: int = None


@dataclass
class ChatMessage:
	id: int | None
	user_id: int
	sender: str
	message: str
	created_at: datetime = get_datetime_now()
	is_read: bool = False
	admin_id: Optional[int] = None


@dataclass
class ChatDialog:
	user_id: int
	full_name: str
	username: Optional[str]
	last_message: str
	last_sender: str
	last_at: datetime
	unread_count: int = 0
