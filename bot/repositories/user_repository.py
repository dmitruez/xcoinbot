from typing import Optional, List
import asyncpg
from . import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
	def __init__(self, pool: asyncpg.Pool):
		super().__init__(pool, 'users', User)

	async def create_table(self) -> None:
		"""Создание таблицы пользователей"""
		query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_banned BOOLEAN DEFAULT FALSE,
            captcha_passed BOOLEAN DEFAULT FALSE,
            should_notify BOOLEAN DEFAULT TRUE,
            join_date TIMESTAMP DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);
        """
		await self._execute(query)

	async def get(self, user_id: int) -> Optional[User]:
		"""Получение пользователя по ID"""
		query = f"SELECT * FROM {self.table_name} WHERE user_id = $1"
		record = await self._fetch(query, user_id)
		return await self._record_to_model(record)

	async def get_by_username(self, username: str) -> Optional[User]:
		"""Получение пользователя по username"""
		query = f"SELECT * FROM {self.table_name} WHERE username = $1"
		record = await self._fetch(query, username)
		return await self._record_to_model(record)

	async def create(self, user: User) -> None:
		"""Создание нового пользователя"""
		query = f"""
        INSERT INTO {self.table_name} 
        (user_id, username, full_name, is_active, is_banned, captcha_passed, should_notify, join_date)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
		await self._execute(
			query,
			user.id, user.username, user.full_name, user.is_active,
			user.is_banned, user.captcha_passed, user.should_notify, user.join_date
		)

	async def update(self, user: User) -> None:
		"""Обновление данных пользователя"""
		query = f"""
        UPDATE {self.table_name} SET
            username = $2,
            full_name = $3,
            is_active = $4,
            is_banned = $5,
            captcha_passed = $6,
            should_notify = $7
        WHERE user_id = $1
        """
		await self._execute(
			query,
			user.id, user.username, user.full_name, user.is_active,
			user.is_banned, user.captcha_passed, user.should_notify
		)

	async def get_all(self) -> List[User]:
		"""Получение всех пользователей"""
		query = f"SELECT * FROM {self.table_name}"
		records = await self._fetch_all(query)
		return await self._records_to_models(records)

	async def get_active_users(self) -> List[User]:
		"""Получение активных пользователей"""
		query = f"""
        SELECT * FROM {self.table_name} 
        WHERE is_active = TRUE AND is_banned = FALSE
        """
		records = await self._fetch_all(query)
		return await self._records_to_models(records)

	async def get_users_for_notification(self) -> List[User]:
		"""Получение пользователей, которым нужно отправлять уведомления"""
		query = f"""
        SELECT * FROM {self.table_name} 
        WHERE is_active = TRUE AND is_banned = FALSE AND should_notify = TRUE
        """
		records = await self._fetch_all(query)
		return await self._records_to_models(records)

	async def ban_user(self, user_id: int) -> None:
		"""Блокировка пользователя"""
		query = f"""
        UPDATE {self.table_name} 
        SET is_banned = TRUE, is_active = FALSE 
        WHERE user_id = $1
        """
		await self._execute(query, user_id)

	async def unban_user(self, user_id: int) -> None:
		"""Разблокировка пользователя"""
		query = f"""
        UPDATE {self.table_name} 
        SET is_banned = FALSE, is_active = TRUE 
        WHERE user_id = $1
        """
		await self._execute(query, user_id)

	async def set_notification_status(self, user_id: int, status: bool) -> None:
		"""Установка статуса уведомлений для пользователя"""
		query = f"""
        UPDATE {self.table_name} 
        SET should_notify = $2 
        WHERE user_id = $1
        """
		await self._execute(query, user_id, status)

	async def mark_captcha_passed(self, user_id: int) -> None:
		"""Отметка прохождения капчи пользователем"""
		query = f"""
        UPDATE {self.table_name} 
        SET captcha_passed = TRUE 
        WHERE user_id = $1
        """
		await self._execute(query, user_id)

	async def count_users(self) -> int:
		"""Получение общего количества пользователей"""
		query = f"SELECT COUNT(*) FROM {self.table_name}"
		async with self.pool.acquire() as conn:
			return await conn.fetchval(query)