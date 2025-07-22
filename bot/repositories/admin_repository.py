from typing import Optional, List

import asyncpg

from .base_repository import BaseRepository
from ..models import Admin


class AdminRepository(BaseRepository[Admin]):

	def __init__(self, pool: asyncpg.Pool):
		super().__init__(pool, 'admins', Admin)

	async def create_table(self) -> None:
		"""Создание таблицы администраторов"""
		query = """
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            full_name TEXT NOT NULL,
            level INTEGER DEFAULT 1
        );
        CREATE INDEX IF NOT EXISTS idx_admins_level ON admins(level);
        """
		await self._execute(query)

	async def get(self, user_id: int) -> Optional[Admin]:
		"""Получение администратора по ID"""
		query = f"SELECT * FROM {self.table_name} WHERE user_id = $1"
		record = await self._fetch(query, user_id)
		return await self._record_to_model(record)

	async def create(self, admin: Admin) -> None:
		"""Добавление нового администратора"""
		query = f"""
        INSERT INTO {self.table_name} 
        (user_id, username, full_name, level)
        VALUES ($1, $2, $3, $4)
        """
		await self._execute(
			query,
			admin.user_id, admin.username, admin.full_name,
			admin.level
		)

	async def update(self, admin: Admin) -> None:
		"""Обновление данных администратора"""
		query = f"""
        UPDATE {self.table_name} SET
            username = $2,
            full_name = $3,
            level = $4
        WHERE user_id = $1
        """
		await self._execute(
			query,
			admin.user_id, admin.username, admin.full_name, admin.level
		)

	async def delete(self, user_id: int) -> None:
		"""Удаление администратора"""
		query = f"DELETE FROM {self.table_name} WHERE user_id = $1"
		await self._execute(query, user_id)

	async def get_all(self) -> List[Admin]:
		"""Получение всех администраторов"""
		query = f"SELECT * FROM {self.table_name}"
		records = await self._fetch_all(query)
		return await self._records_to_models(records)

	async def is_admin(self, user_id: int) -> bool:
		"""Проверка, является ли пользователь администратором"""
		query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE user_id = $1)"
		async with self.pool.acquire() as conn:
			return await conn.fetchval(query, user_id)

	async def get_admins_with_level(self, min_level: int) -> List[Admin]:
		"""Получение администраторов с минимальным уровнем доступа"""
		query = f"SELECT * FROM {self.table_name} WHERE level >= $1"
		records = await self._fetch_all(query, min_level)
		return await self._records_to_models(records)

	async def update_level(self, user_id: int, level: int) -> None:
		query = f"""UPDATE {self.table_name} SET level = $1
					WHERE user_id = $2"""
		await self._execute(query, level, user_id)
