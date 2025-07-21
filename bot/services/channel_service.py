from typing import Optional, List

from aiogram import Bot
from aiogram.types import Chat

from ..models import Channel
from ..repositories.channel_repository import ChannelRepository
from ..utils.loggers import services as logger


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
			logger.exception(f"Error getting main channel: {e}")
			return None

	async def get_backup_channel(self) -> Optional[Channel]:
		"""Получение резервного канала"""
		try:
			return await self.channel_repo.get_backup_channel()
		except Exception as e:
			logger.exception(f"Error getting backup channel: {e}")
			return None

	async def get_channel(self, channel_id: int) -> Optional[Channel]:
		"""Получение канала по id"""
		try:
			return await self.channel_repo.get(channel_id)
		except Exception as e:
			logger.exception(f"Error getting channel: {e}")
			return None

	async def add_new_channel(self, channel: Channel):
		"""Добавление нового чата"""
		try:
			await self.channel_repo.create(channel)
		except Exception as e:
			logger.exception(f"Error adding new channel: {e}")

	async def delete_channel(self, channel: Channel):
		"""Удаление канала из бд"""
		try:
			await self.channel_repo.delete(channel.channel_id)

		except Exception as e:
			logger.exception(f"Error deleting channel: {e}")

	async def update_channel(self, channel: Channel):
		"""Обновление сведений о канале (в основном для добавления пригласительной ссылки)"""
		try:
			await self.channel_repo.update(channel)
		except Exception as e:
			logger.exception(f"Error updating channel {e}")

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
			logger.exception(f"Error setting main channel {channel_id}: {e}")
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
			logger.exception(f"Error setting backup channel {channel_id}: {e}")
			return False

	async def _get_chat_info(self, channel_id: int) -> Optional[Chat]:
		"""Получение информации о канале"""
		try:
			return await self.bot.get_chat(channel_id)
		except Exception as e:
			logger.exception(f"Error getting chat info for {channel_id}: {e}")
			return None

	async def get_channel_list(self) -> List[Channel]:
		"""Получение списка всех каналов"""
		try:
			channels = await self.channel_repo.get_all()
			return channels
		except Exception as e:
			logger.exception(f"Error getting channel list: {e}")
			return []

	async def check_subscription(self, user_id: int) -> bool:
		"""Проверяет подписку пользователя на резервный канал"""
		try:
			# Получаем резервный канал
			backup_channel = await self.channel_repo.get_backup_channel()
			if not backup_channel:
				logger.warning("Backup channel not set")
				return True  # Если канал не настроен, пропускаем проверку

			# Проверяем статус подписки
			member = await self.bot.get_chat_member(
				chat_id=backup_channel.channel_id,
				user_id=user_id
			)

			return member.status in ['member', 'administrator', 'creator']
		except Exception as e:
			logger.exception(f"Subscription check failed for user {user_id}: {str(e)}")
			return False
