from datetime import datetime
from typing import Optional, List

import asyncpg

from .base_repository import BaseRepository
from ..models import User


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
            join_date TIMESTAMP DEFAULT NOW(),
            banned_when TIMESTAMP DEFAULT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        CREATE INDEX IF NOT EXISTS idx_users_banned ON users(is_banned);
        """
		await self._execute(query)

	async def get_by_id(self, user_id: int) -> Optional[User]:
		"""Получение пользователя по ID"""
		query = f"SELECT * FROM {self.table_name} WHERE user_id = $1"
		record = await self._fetch(query, user_id)
		return await self._record_to_model(record)

	async def get_by_username(self, query: str, limit: int = 12) -> List[User]:
		"""Поиск пользователей по username (без @)"""
		query = query.lower().strip()
		sql = f"""
	    SELECT * FROM {self.table_name}
	    WHERE username IS NOT NULL 
	    AND LOWER(username) LIKE $1 || '%'
	    LIMIT $2
	    """
		records = await self._fetch_all(sql, query, limit)
		return await self._records_to_models(records)

	async def get_by_nickname(self, query: str, limit: int = 12) -> List[User]:
		"""Поиск пользователей по nickname (имя + фамилия)"""
		query = query.lower().strip()
		sql = f"""
	    SELECT * FROM {self.table_name}
	    WHERE LOWER(full_name) LIKE '%' || $1 || '%'
	    LIMIT $2
	    """
		records = await self._fetch_all(sql, query, limit)
		return await self._records_to_models(records)

	async def create(self, user: User) -> None:
		"""Создание нового пользователя"""
		query = f"""
        INSERT INTO {self.table_name} 
        (user_id, username, full_name, is_active, is_banned, captcha_passed, should_notify, join_date)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
		await self._execute(
			query,
			user.user_id, user.username, user.full_name, user.is_active,
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
			user.user_id, user.username, user.full_name, user.is_active,
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
        WHERE is_active = TRUE AND is_banned = FALSE AND should_notify = TRUE AND captcha_passed = TRUE
        """
		records = await self._fetch_all(query)
		return await self._records_to_models(records)

	async def ban_user(self, user_id: int) -> None:
		"""Блокировка пользователя"""
		query = f"""
        UPDATE {self.table_name} 
        SET is_banned = TRUE, is_active = FALSE, banned_when = now()
        WHERE user_id = $1
        """
		await self._execute(query, user_id)

	async def unban_user(self, user_id: int) -> None:
		"""Разблокировка пользователя"""
		query = f"""
        UPDATE {self.table_name} 
        SET is_banned = FALSE, is_active = TRUE, banned_when = null;
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

	async def count_active_users(self) -> int:
		"""Получение активных пользователей"""
		query = f"""
		SELECT COUNT(*) FROM {self.table_name} 
		WHERE is_active = TRUE AND is_banned = FALSE
		"""
		async with self.pool.acquire() as conn:
			return await conn.fetchval(query)

	async def count_banned_users(self) -> List[User]:
		async with self.pool.acquire() as conn:
			return await conn.fetchval(
				f"SELECT COUNT(*) FROM {self.table_name} WHERE is_banned = TRUE"
			)

	async def count_users_period(self, start_date: datetime, end_date: datetime) -> int:
		"""Количество новых пользователей за период"""
		async with self.pool.acquire() as conn:
			return await conn.fetchval(
				f"SELECT COUNT(*) FROM {self.table_name} WHERE join_date BETWEEN $1 AND $2",
				start_date, end_date
			)

	async def count_active_period(self, start_date: datetime, end_date: datetime) -> int:
		"""Количество активных пользователей за период"""
		async with self.pool.acquire() as conn:
			return await conn.fetchval(
				f"SELECT COUNT(*) FROM {self.table_name} WHERE is_active = TRUE AND join_date BETWEEN $1 AND $2",
				start_date, end_date
			)

	async def count_banned_period(self, start_date: datetime, end_date: datetime) -> int:
		"""Количество забаненных пользователей за период"""
		async with self.pool.acquire() as conn:
			return await conn.fetchval(
				f"SELECT COUNT(*) FROM {self.table_name} WHERE is_banned = TRUE AND banned_when BETWEEN $1 AND $2",
				start_date, end_date
			)
	
	async def get_all_users_formatted(self) -> str:
		"""Получение всех пользователей в формате для TXT файла"""
		query = f"SELECT * FROM {self.table_name}"
		records = await self._fetch_all(query)
		
		if not records:
			return ""
		
		result = []
		for record in records:
			user = await self._record_to_model(record)
			result.append(
				f"ID: {user.user_id}\n"
				f"Username: @{user.username if user.username else 'нет'}\n"
				f"Имя: {user.full_name}\n"
				f"Дата регистрации: {user.join_date.strftime('%d.%m.%Y %H:%M')}\n"
				f"Активен: {'🟢 Да' if user.is_active else '🔴 Нет'}\n"
				f"Уведомления: {'🟢 Включены' if user.should_notify else '🔴 Выключены'}\n"
				"----------------------------------------"
			)
		
		return "\n\n".join(result)