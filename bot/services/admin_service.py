import io
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from ..models import Admin
from ..repositories import UserRepository, ChannelRepository
from ..repositories.admin_repository import AdminRepository
from ..utils.loggers import services as logger


class AdminService:
	"""Сервис для работы с администраторами"""

	def __init__(self, admin_repo: AdminRepository, user_repo: UserRepository, channel_repo: ChannelRepository):
		self.admin_repo = admin_repo
		self.user_repo = user_repo
		self.channel_repo = channel_repo

	async def get_admin(self, user_id: int) -> Optional[Admin]:
		"""Получение администратора по ID"""
		try:
			return await self.admin_repo.get(user_id)
		except Exception as e:
			logger.error(f"Error getting admin {user_id}: {e}")
			return None

	async def add_admin(self, admin: Admin) -> bool:
		"""Добавление нового администратора"""
		if admin.level not in (1, 2, 3):
			return False

		try:
			await self.admin_repo.create(admin)
			logger.info(f"Added new admin: {admin.user_id} (level {admin.level})")
			return True
		except Exception as e:
			logger.error(f"Error adding admin {admin.user_id}: {e}")
			return False

	async def update_admin_level(self, user_id: int, new_level: int) -> bool:
		"""Изменение уровня администратора"""
		if new_level not in (1, 2, 3):
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
			super_admins = [a for a in admins if a.level > 1]
			return regular, super_admins
		except Exception as e:
			logger.error(f"Error listing admins: {e}")
			return [], []

	async def get_stats(self) -> dict:
		"""Получение статистики бота"""
		total_users = await self.user_repo.count_users()
		active_users = await self.user_repo.count_active_users()
		banned_users = await self.user_repo.count_banned_users()
		channels_count = await self.channel_repo.count_channels()

		main_channel = await self.channel_repo.get_main_channel()
		backup_channel = await self.channel_repo.get_backup_channel()

		return {
			'total_users': total_users,
			'active_users': active_users,
			'banned_users': banned_users,
			'channels_count': channels_count,
			'main_channel': f"<a href='{main_channel.link}'>{main_channel.title}</a>" if main_channel else "Не установлен",
			'backup_channel': f"<a href='{backup_channel.link}'>{backup_channel.title}</a>" if backup_channel else "Не установлен"
		}

	async def get_period_stats(self, start_date: datetime, end_date: datetime) -> Dict[str, any]:
		"""Получение статистики за указанный период"""
		return {
			'new_users': await self.user_repo.count_users_period(start_date, end_date),
			'active_users': await self.user_repo.count_active_period(start_date, end_date),
			'banned_users': await self.user_repo.count_banned_period(start_date, end_date),
		}

	async def get_daily_stats(self, days: int = 7) -> List[Dict[str, any]]:
		"""Получение статистики по дням"""
		stats = []
		today = datetime.now().date()

		for i in range(days, 0, -1):
			date = today - timedelta(days=i)
			start = datetime(date.year, date.month, date.day)
			end = start + timedelta(days=1)

			day_stats = await self.get_period_stats(start, end)
			stats.append({
				'date': date.strftime("%Y-%m-%d"),
				'new_users': day_stats['new_users'],
				'active_users': day_stats['active_users'],
				'banned_users': day_stats['banned_users']
			})

		return stats

	@staticmethod
	async def get_logs() -> List | None:
		"""Получение файла логов"""
		try:
			log_dir = Path("logs")
			if not log_dir.exists():
				return None

			log_files = list(map(lambda x: x.stem, sorted(log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)))
			if not log_files:
				return None

			return log_files
		except Exception as e:
			logger.error(f"Error getting logs: {str(e)}")
			return None

	async def create_backup(self) -> io.BytesIO | None:
		"""Создание бэкапа базы данных"""
		pass
