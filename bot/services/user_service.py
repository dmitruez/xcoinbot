from typing import List, Optional, Dict

from ..models import User
from ..repositories.user_repository import UserRepository
from ..utils.loggers import services as logger


class UserService:
	"""Сервис для работы с пользователями"""

	def __init__(self, user_repo: UserRepository):
		self.user_repo = user_repo

	async def get_user(self, user_id: int) -> Optional[User]:
		"""Получение пользователя по ID"""
		try:
			return await self.user_repo.get(user_id)
		except Exception as e:
			logger.error(f"Error getting user {user_id}: {e}")
			return None

	async def create_user(self, user) -> User:
		"""Создание нового пользователя"""

		try:
			await self.user_repo.create(user)
			logger.info(f"Created new user: {user.user_id}")
			return user
		except Exception as e:
			logger.error(f"Error creating user {user.user_id}: {e}")
			raise

	async def ban_user(self, user_id: int) -> bool:
		"""Блокировка пользователя"""
		try:
			await self.user_repo.ban_user(user_id)
			logger.info(f"Banned user: {user_id}")
			return True
		except Exception as e:
			logger.error(f"Error banning user {user_id}: {e}")
			return False

	async def unban_user(self, user_id: int) -> bool:
		"""Разблокировка пользователя"""
		try:
			await self.user_repo.unban_user(user_id)
			logger.info(f"Unbanned user: {user_id}")
			return True
		except Exception as e:
			logger.error(f"Error unbanning user {user_id}: {e}")
			return False

	async def mark_captcha_passed(self, user_id: int) -> bool:
		"""Отметка прохождения капчи"""
		try:
			await self.user_repo.mark_captcha_passed(user_id)
			return True
		except Exception as e:
			logger.error(f"Error marking captcha passed for {user_id}: {e}")
			return False

	async def set_notification_status(self, user_id: int, status: bool) -> bool:
		"""Установка статуса уведомлений"""
		try:
			await self.user_repo.set_notification_status(user_id, status)
			return True
		except Exception as e:
			logger.error(f"Error setting notification status for {user_id}: {e}")
			return False

	async def get_users_for_notification(self) -> List[User]:
		"""Получение пользователей для уведомлений"""
		try:
			return await self.user_repo.get_users_for_notification()
		except Exception as e:
			logger.error(f"Error getting users for notification: {e}")
			return []

	async def count_users(self) -> Dict[str, int]:
		"""Получение статистики пользователей"""
		try:
			total = await self.user_repo.count_users()
			active = await self.user_repo.count_active_users()
			return {
				'total': total,
				'active': active
			}
		except Exception as e:
			logger.exception(f"Error counting users: {e}")
		return {'total': 0, 'active': 0}

	async def users_list(self) -> List[User]:
		try:
			return await self.user_repo.get_all()
		except Exception as e:
			logger.exception(f"Error getting all users: {e}")
