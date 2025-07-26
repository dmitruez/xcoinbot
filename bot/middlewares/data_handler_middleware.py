from typing import Dict, Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, Update, TelegramObject


class DataHandlerMiddleware(BaseMiddleware):
	def __init__(self, **kwargs):
		self.kwargs = kwargs

	async def __call__(
			self,
			handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
			event: TelegramObject,
			data: dict
	) -> Any:
		data.update(self.kwargs)
		return await handler(event, data)
