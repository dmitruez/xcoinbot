# Проверка подписки на резерв каннал

# Standard library
from typing import Any, Awaitable, Callable, Dict

# Third party
from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import Message

from ..services import Services


class SubscriberMiddleware(BaseMiddleware):

	def __init__(self, bot: Bot, services: Services):
		self.bot = bot
		self.services = services

	async def __call__(
			self,
			handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
			event: Message,
			data: Dict[str, Any],
	) -> Any:

		if event.text and event.text.startswith(('/start', '/help')):
			return

		if not await self.services.channel.check_subscription(event.from_user.id):
			backup_channel = await self.services.channel.get_backup_channel()
			if backup_channel:
				await event.answer(
					"⚠ Для использования бота необходимо подписаться на резервный канал:\n"
					f"@{backup_channel.username}" if backup_channel.username else
					f"Ссылка: https://t.me/c/{str(backup_channel.channel_id)[4:]}"
				)
			else:
				await event.answer("⚠ Резервный канал не настроен. Обратитесь к администратору.")

			raise CancelHandler()

		return await handler(event, data)
