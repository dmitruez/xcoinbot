from typing import Dict, Any, Callable, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message


class DataHandlerMiddleware(BaseMiddleware):
	def __init__(self, **kwargs):
		self.kwargs = kwargs

	async def __call__(
			self,
			handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
			event: Message,
			data: dict
	) -> Any:
		data.update(self.kwargs)
		return await handler(event, data)
