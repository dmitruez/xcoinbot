# Проверка прав админа

# Standard library
from typing import Any, Awaitable, Callable, Dict

# Third party
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from ..config import Config
from ..services import Services


access_map = {
	'/start': 0,
	'/channel': 0,
	'/stats': 1,
	'/admin': 1,
	'/ban': 2,
	'/unban': 2,
	'/edit_channels': 2,
	'/edit_notification': 2,
	'/logs': 3,
	'/backup': 3
}


class AdminMiddleware(BaseMiddleware):

	def __init__(self, services: Services) -> None:
		self.services = services

	async def __call__(
			self,
			handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
			event: Message,
			data: Dict[str, Any],
	) -> Any:
		if not is_command(event):
			return await handler(event, data)

		# Проверяем, требует ли команда админских прав
		command = event.text
		required_level = get_command_access_level(command)

		if required_level > 0:
			admin = await self.services.admin.get_admin(event.from_user.id)
			data['admin'] = admin  # Добавляем объект админа в data

			# Проверяем права пользователя
			if event.from_user.id in Config.DEVELOPERS_IDS:
				return await handler(event, data)

			if not admin or admin.level < required_level:
				await event.answer("⛔ У вас недостаточно прав для этой команды")
				return

		return await handler(event, data)


class AdminCallbackMiddleware(BaseMiddleware):
	def __init__(self, services: Services) -> None:
		self.services = services

	async def __call__(
			self,
			handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
			event: CallbackQuery,
			data: Dict[str, Any],
	) -> Any:
		admin = await self.services.admin.get_admin(event.from_user.id)
		data['admin'] = admin  # Добавляем объект админа в data
		return await handler(event, data)


def get_command_access_level(command: str) -> int:
	"""Возвращает требуемый уровень доступа для команды"""
	return access_map.get(command, 0)  # 0 - не требует прав


def is_command(event: Message) -> bool:
	"""Возвращает булевое значение является ли сообщение командой"""
	return event.text in access_map.keys()
