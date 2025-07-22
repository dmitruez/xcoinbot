# Логика подписчиков

from typing import Optional, Tuple

from aiogram import Bot

from ..models import User
from ..repositories.channel_repository import ChannelRepository
from ..repositories.user_repository import UserRepository
from ..utils.loggers import services as logger


class SubscriptionService:
	"""Сервис для работы с подписками"""

	def __init__(self, bot: Bot, user_repo: UserRepository, channel_repo: ChannelRepository):
		self.bot = bot
		self.user_repo = user_repo
		self.channel_repo = channel_repo

	async def check_subscription(self, user_id: int) -> bool:
		"""Проверка подписки пользователя на резервный канал"""
		try:
			backup_channel = await self.channel_repo.get_backup_channel()
			if not backup_channel:
				return True  # Если резервный канал не установлен, пропускаем проверку

			member = await self.bot.get_chat_member(
				chat_id=backup_channel.channel_id,
				user_id=user_id
			)
			return member.status in ['member', 'administrator', 'creator']
		except Exception as e:
			logger.error(f"Error checking subscription for {user_id}: {e}")
			return False

	async def verify_user(self, user_id: int, username: Optional[str], full_name: str) -> Tuple[bool, Optional[User]]:
		"""
		Верификация пользователя (проверка подписки и капчи)
		:return: Кортеж (успех верификации, объект User)
		"""
		try:
			# Проверяем/создаем пользователя
			user = await self.user_repo.get_by_id(user_id)
			if not user:
				user = await self.user_repo.create(User(
					user_id=user_id,
					username=username,
					full_name=full_name,
					is_active=True,
					should_notify=True
				))

			# Проверяем подписку
			if not await self.check_subscription(user_id):
				return False, user

			# Проверяем капчу
			if not user.captcha_passed:
				return False, user

			return True, user
		except Exception as e:
			logger.error(f"Error verifying user {user_id}: {e}")
			return False, None
