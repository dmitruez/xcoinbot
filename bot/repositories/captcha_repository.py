from typing import Optional

import asyncpg

from .base_repository import BaseRepository
from ..models import Captcha


class CaptchaRepository(BaseRepository[Captcha]):
	def __init__(self, pool: asyncpg.Pool):
		super().__init__(pool, 'captcha', Captcha)

	async def create_table(self) -> None:
		"""Создание таблицы капчи"""
		query = """
        CREATE TABLE IF NOT EXISTS captcha (
            user_id BIGINT PRIMARY KEY,
            text TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
		await self._execute(query)

	async def get(self, user_id: int) -> Optional[Captcha]:
		"""Получение капчи пользователя"""
		query = f"SELECT * FROM {self.table_name} WHERE user_id = $1"
		record = await self._fetch(query, user_id)
		return await self._record_to_model(record)

	async def create(self, captcha: Captcha) -> None:
		"""Создание новой капчи"""
		query = f"""
        INSERT INTO {self.table_name} 
        (user_id, text, attempts, created_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO UPDATE SET
            text = EXCLUDED.text,
            attempts = EXCLUDED.attempts
        """
		await self._execute(
			query,
			captcha.user_id, captcha.text, captcha.attempts, captcha.created_at
		)

	async def increment_attempts(self, user_id: int) -> None:
		"""Увеличение счетчика попыток"""
		query = f"""
        UPDATE {self.table_name} 
        SET attempts = attempts + 1 
        WHERE user_id = $1
        """
		await self._execute(query, user_id)

	async def delete(self, user_id: int) -> None:
		"""Удаление капчи пользователя"""
		query = f"DELETE FROM {self.table_name} WHERE user_id = $1"
		await self._execute(query, user_id)

	async def get_attempts(self, user_id: int) -> int:
		"""Получение количества попыток"""
		query = f"SELECT attempts FROM {self.table_name} WHERE user_id = $1"
		async with self.pool.acquire() as conn:
			return await conn.fetchval(query, user_id) or 0
