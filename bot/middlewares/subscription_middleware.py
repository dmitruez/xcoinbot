# Проверка подписки на резерв каннал

from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from ..services import Services


class SubscriptionMiddleware(BaseMiddleware):

	def __init__(self, services: Services) -> None:
		self.services = services

	async def __call__(
			self,
			handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
			event: Message,
			data: Dict[str, Any]
	) -> Any:

		user = await self.services.user.get_user_by_id(event.from_user.id)
		if user:
			if not user.should_notify or user.is_banned:
				await event.answer(text="❌ Вам отключили использование бота ❌")
				return

		# Пропускаем команды /start и /help
		if event.text and event.text.startswith(('/start', '/help')):
			return await handler(event, data)



		# Если капча не пройдена или пользователь не существует
		if not user or not user.captcha_passed:
			return await handler(event, data)

		# Проверяем подписку
		if not await self.services.channel.check_subscription(event.from_user.id):
			backup_channel = await self.services.channel.get_backup_channel()
			if backup_channel:
				await event.answer(
					"⚠ Для использования бота необходимо подписаться на резервный канал:\n" 
					f"Ссылка: {backup_channel.link}"
				)
			else:
				await event.answer("⚠ Резервный канал не настроен. Обратитесь к администратору.")
			return

		return await handler(event, data)