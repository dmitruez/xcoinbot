from typing import TypeVar, Generic, Optional, List, Union

import asyncpg
from asyncpg.pool import Pool


T = TypeVar('T')


class BaseRepository(Generic[T]):
	"""Базовый класс репозитория с общими методами"""

	def __init__(self, pool: asyncpg.Pool, table_name: str, model_class: type):
		self.pool: Union[Pool, None] = pool
		self.table_name = table_name
		self.model_class = model_class

	async def _execute(self, query: str, *args) -> None:
		"""Выполнение запроса без возврата результата"""
		async with self.pool.acquire() as conn:
			await conn.execute(query, *args)

	async def _fetch(self, query: str, *args) -> Optional[asyncpg.Record]:
		"""Получение одной записи"""
		async with self.pool.acquire() as conn:
			return await conn.fetchrow(query, *args)

	async def _fetch_all(self, query: str, *args) -> List[asyncpg.Record]:
		"""Получение всех записей"""
		async with self.pool.acquire() as conn:
			return await conn.fetch(query, *args)

	async def _record_to_model(self, record: Optional[asyncpg.Record]) -> Optional[T]:
		"""Преобразование записи БД в модель"""
		return self.model_class(**dict(record)) if record else None

	async def _records_to_models(self, records: List[asyncpg.Record]) -> List[T]:
		"""Преобразование списка записей в список моделей"""
		return [self.model_class(**dict(record)) for record in records]
