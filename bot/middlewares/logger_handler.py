
# Standard library
from typing import Any, Awaitable, Callable, Dict

# Third party
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update, TelegramObject

from ..utils.loggers import handlers as logger



class LoggerMiddleware(BaseMiddleware):
	async def __call__(
			self,
			handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
			event: TelegramObject,
			data: Dict[str, Any],
	) -> Any:
		user = event.event.from_user
		event_type = event.event_type
		result = await handler(event, data)

		handled = False
		if result is None:
			handled = True
		if event_type == 'message':
			logger.info(f"id={user.id}; username=@{user.username}; action=message; text={event.event.text}; handled={handled};")
		elif event_type == 'callback_query':
			logger.info(f"id={user.id}; username=@{user.username}; action=callback; data={event.event.data}; handled={handled};")
