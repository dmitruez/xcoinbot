from typing import Optional, List, Dict

from aiogram import Bot
from aiogram.types import Chat

from ..models import Channel
from ..repositories.channel_repository import ChannelRepository
from ..utils.logger import logger


class ChannelService:
	"""Сервис для работы с каналами"""

	def __init__(self, bot: Bot, channel_repo: ChannelRepository):
		self.bot = bot
		self.channel_repo = channel_repo

	async def get_main_channel(self) -> Optional[Channel]:
		"""Получение основного канала"""
		try:
			return await self.channel_repo.get_main_channel()
		except Exception as e:
			logger.error(f"Error getting main channel: {e}")
			return None

	async def get_backup_channel(self) -> Optional[Channel]:
		"""Получение резервного канала"""
		try:
			return await self.channel_repo.get_backup_channel()
		except Exception as e:
			logger.error(f"Error getting backup channel: {e}")
			return None

	async def set_main_channel(self, channel_id: int) -> bool:
		"""Установка основного канала"""
		try:
			chat = await self._get_chat_info(channel_id)
			if not chat:
				return False


			await self.channel_repo.set_main_channel(channel_id)
			logger.info(f"Set main channel: {channel_id}")
			return True
		except Exception as e:
			logger.error(f"Error setting main channel {channel_id}: {e}")
			return False

	async def set_backup_channel(self, channel_id: int) -> bool:
		"""Установка резервного канала"""
		try:
			chat = await self._get_chat_info(channel_id)
			if not chat:
				return False

			await self.channel_repo.set_backup_channel(channel_id)
			logger.info(f"Set backup channel: {channel_id}")
			return True
		except Exception as e:
			logger.error(f"Error setting backup channel {channel_id}: {e}")
			return False

	async def _get_chat_info(self, channel_id: int) -> Optional[Chat]:
		"""Получение информации о канале"""
		try:
			return await self.bot.get_chat(channel_id)
		except Exception as e:
			logger.error(f"Error getting chat info for {channel_id}: {e}")
			return None

	async def get_channel_list(self) -> List[Dict]:
		"""Получение списка всех каналов"""
		try:
			channels = await self.channel_repo.get_all()
			return [{
				'id': channel.id,
				'title': channel.title,
				'is_main': channel.is_main,
				'is_backup': channel.is_backup
			} for channel in channels]
		except Exception as e:
			logger.error(f"Error getting channel list: {e}")
			return []
