from typing import List, Optional, Tuple
from ..models import Admin
from ..repositories.admin_repository import AdminRepository
from ..utils.logger import logger


class AdminService:
	"""Сервис для работы с администраторами"""

	def __init__(self, admin_repo: AdminRepository):
		self.admin_repo = admin_repo

	async def get_admin(self, user_id: int) -> Optional[Admin]:
		"""Получение администратора по ID"""
		try:
			return await self.admin_repo.get(user_id)
		except Exception as e:
			logger.error(f"Error getting admin {user_id}: {e}")
			return None

	async def add_admin(self, user_id: int, username: Optional[str], full_name: str, level: int = 1) -> bool:
		"""Добавление нового администратора"""
		if level not in (1, 2):
			return False

		admin = Admin(
			user_id=user_id,
			username=username,
			full_name=full_name,
			level=level
		)

		try:
			await self.admin_repo.create(admin)
			logger.info(f"Added new admin: {user_id} (level {level})")
			return True
		except Exception as e:
			logger.error(f"Error adding admin {user_id}: {e}")
			return False

	async def update_admin_level(self, user_id: int, new_level: int) -> bool:
		"""Изменение уровня администратора"""
		if new_level not in (1, 2):
			return False

		try:
			await self.admin_repo.update_level(user_id, new_level)
			logger.info(f"Updated admin {user_id} level to {new_level}")
			return True
		except Exception as e:
			logger.error(f"Error updating admin {user_id} level: {e}")
			return False

	async def remove_admin(self, user_id: int) -> bool:
		"""Удаление администратора"""
		try:
			await self.admin_repo.delete(user_id)
			logger.info(f"Removed admin: {user_id}")
			return True
		except Exception as e:
			logger.error(f"Error removing admin {user_id}: {e}")
			return False

	async def list_admins(self) -> Tuple[List[Admin], List[Admin]]:
		"""Получение списка администраторов"""
		try:
			admins = await self.admin_repo.get_all()
			regular = [a for a in admins if a.level == 1]
			super_admins = [a for a in admins if a.level == 2]
			return regular, super_admins
		except Exception as e:
			logger.error(f"Error listing admins: {e}")
			return [], []