import csv
from datetime import datetime
from io import StringIO
from typing import List, Optional, Dict, Tuple

from ..models import User
from ..repositories import AdminRepository
from ..repositories.user_repository import UserRepository
from ..utils.loggers import services as logger


class UserService:
	"""Сервис для работы с пользователями"""

	def __init__(self, user_repo: UserRepository, admin_repo: AdminRepository):
		self.user_repo = user_repo
		self.admin_repo = admin_repo

	async def get_user_by_id(self, user_id: int=None) -> Optional[User]:
		"""Получение пользователя по ID"""
		try:
			return await self.user_repo.get_by_id(user_id)
		except Exception as e:
			logger.error(f"Error getting user {user_id}: {e}")
			return None

	async def search_users(self, search_type: str, query: str) -> List[User]:
		"""Поиск пользователей по типу поиска"""
		query = query.strip()

		if search_type == "username":
			return await self.user_repo.get_by_username(query)
		elif search_type == "nickname":
			return await self.user_repo.get_by_nickname(query)
		elif search_type == "id":
			if query.isdigit():
				user = await self.user_repo.get_by_id(int(query))
				return [user] if user else []
		return []

	async def format_user_info(self, user: User) -> Tuple[str, bool, int]:
		"""Форматирование информации о пользователе"""
		admin = await self.admin_repo.get(user.user_id)

		if admin:
			admin_info = f"\n👑 Админ: Да (Уровень: {admin.level})"
		else:
			admin_info = "\n👑 Админ: Нет"

		return (
			f"👤 ID: <code>{user.user_id}</code>\n"
			f"🆔 Username: @{user.username if user.username else 'нет'}\n"
			f"👤 Имя: {user.full_name}\n"
			f"📅 Дата регистрации: {user.join_date.strftime('%d.%m.%Y')}\n"
			f"🔒 Статус бота: {'🟢 Активен' if user.is_active else '🔴 Заблокирован'}\n"
			f"Уведомления: {'🟢 Включены' if user.should_notify else '🔴 Выключены'}\n"
			f"{admin_info}"
		), True if admin else False, admin.level if admin else None

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
	
	async def get_users_file(self, format_type: str) -> Tuple[str, str, str]:
		"""
		Получение списка пользователей в выбранном формате
		Возвращает: (content, filename, caption)
		"""
		try:
			users = await self.user_repo.get_all()
			total_users = len(users)
			active_users = sum(1 for u in users if u.is_active)
			
			header_info = (
				f"# Всего пользователей: {total_users}\n"
				f"# Активных: {active_users}\n"
				f"# Неактивных: {total_users - active_users}\n"
				f"# Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
			)
			
			if format_type == "txt":
				return self._format_txt(users, header_info)
			elif format_type == "csv":
				return self._format_csv(users, header_info)
			else:
				raise ValueError("Неизвестный формат")
		
		except Exception as e:
			logger.error(f"Ошибка при формировании списка пользователей: {e}")
			return "❌ Не удалось сформировать список", "error.txt", "Ошибка"
	
	def _format_txt(self, users: List[User], header: str) -> Tuple[str, str, str]:
		"""Форматирование в красивый TXT"""
		result = [header, "\n" + "=" * 50 + "\n"]
		
		for i, user in enumerate(users, 1):
			user_info = (
					f"👤 Пользователь #{i}\n"
					f"🆔 ID: {user.user_id}\n"
					f"👤 Имя: {user.full_name}\n"
					f"📱 Username: @{user.username if user.username else 'N/A'}\n"
					f"📅 Дата регистрации: {user.join_date.strftime('%d.%m.%Y %H:%M')}\n"
					f"🔒 Статус: {'🟢 Активен' if user.is_active else '🔴 Заблокирован'}\n"
					f"🔔 Уведомления: {'🟢 Вкл' if user.should_notify else '🔴 Выкл'}\n\n"
					+ "⎯" * 30
			)
			result.append(user_info)
		
		filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
		caption = "📋 Список пользователей (TXT)"
		return "\n\n".join(result), filename, caption
	
	def _format_csv(self, users: List[User], header: str) -> Tuple[str, str, str]:
		"""Форматирование в CSV"""
		# Создаем CSV в памяти
		output = StringIO()
		writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		
		# Заголовки CSV
		writer.writerow([
			"ID", "Full Name", "Username", "Registration Date",
			"Is Active", "Notifications"
		])
		
		# Данные пользователей
		for user in users:
			writer.writerow([
				user.user_id,
				user.full_name,
				f"@{user.username}" if user.username else "",
				user.join_date.strftime('%Y-%m-%d %H:%M'),
				"Yes" if user.is_active else "No",
				"Yes" if user.should_notify else "No"
			])
		
		# Добавляем header как комментарий
		csv_data = output.getvalue().replace('\r\n', '\n').replace('\r', '\n')
		csv_content = f"{header}\n{csv_data}"
		
		filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
		caption = "📊 Список пользователей (CSV)"
		return csv_content, filename, caption
	
