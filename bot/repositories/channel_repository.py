from typing import Optional, List

import asyncpg

from .base_repository import BaseRepository
from ..models import Channel


class ChannelRepository(BaseRepository[Channel]):
	def __init__(self, pool: asyncpg.Pool):
		super().__init__(pool, 'channels', Channel)

	async def create_table(self) -> None:
		"""Создание таблицы каналов"""
		query = """
        CREATE TABLE IF NOT EXISTS channels (
            channel_id BIGINT PRIMARY KEY,
            title TEXT NOT NULL,
            username TEXT,
            link TEXT,
            is_main BOOLEAN DEFAULT FALSE,
            is_backup BOOLEAN DEFAULT FALSE
        );
        CREATE INDEX IF NOT EXISTS idx_channels_main ON channels(is_main);
        CREATE INDEX IF NOT EXISTS idx_channels_backup ON channels(is_backup);
        """
		await self._execute(query)

	async def get(self, channel_id: int) -> Optional[Channel]:
		"""Получение канала по ID"""
		query = f"SELECT * FROM {self.table_name} WHERE channel_id = $1"
		record = await self._fetch(query, channel_id)
		return await self._record_to_model(record)

	async def get_by_username(self, username: str) -> Optional[Channel]:
		"""Получение канала по username"""
		query = f"SELECT * FROM {self.table_name} WHERE username = $1"
		record = await self._fetch(query, username)
		return await self._record_to_model(record)

	async def get_main_channel(self) -> Optional[Channel]:
		"""Получение основного канала"""
		query = f"SELECT * FROM {self.table_name} WHERE is_main = TRUE LIMIT 1"
		record = await self._fetch(query)
		return await self._record_to_model(record)

	async def get_backup_channel(self) -> Optional[Channel]:
		"""Получение резервного канала"""
		query = f"SELECT * FROM {self.table_name} WHERE is_backup = TRUE LIMIT 1"
		record = await self._fetch(query)
		return await self._record_to_model(record)

	async def create(self, channel: Channel) -> None:
		"""Создание нового канала"""
		query = f"""
        INSERT INTO {self.table_name} 
        (channel_id, title, username, link, is_main, is_backup)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
		await self._execute(
			query,
			channel.channel_id, channel.title, channel.username,
			channel.link, channel.is_main, channel.is_backup
		)

	async def update(self, channel: Channel) -> None:
		"""Обновление данных канала"""
		query = f"""
        UPDATE {self.table_name} SET
            title = $2,
            username = $3,
            link = $4,
            is_main = $5,
            is_backup = $6
        WHERE channel_id = $1
        """
		await self._execute(
			query,
			channel.channel_id, channel.title, channel.username,
			channel.link, channel.is_main, channel.is_backup
		)

	async def set_main_channel(self, channel_id: int) -> None:
		"""Установка канала как основного"""
		# Сначала сбрасываем все main каналы
		await self._execute(f"UPDATE {self.table_name} SET is_main = FALSE")

		# Затем устанавливаем новый main канал
		query = f"""
        UPDATE {self.table_name} 
        SET is_main = TRUE, is_backup = FALSE
        WHERE channel_id = $1
        """
		await self._execute(query, channel_id)

	async def set_backup_channel(self, channel_id: int) -> None:
		"""Установка канала как резервного"""
		# Сначала сбрасываем все backup каналы
		await self._execute(f"UPDATE {self.table_name} SET is_backup = FALSE")

		# Затем устанавливаем новый backup канал
		query = f"""
        UPDATE {self.table_name} 
        SET is_backup = TRUE 
        WHERE channel_id = $1
        """
		await self._execute(query, channel_id)

	async def get_all(self) -> List[Channel]:
		"""Получение всех каналов"""
		query = f"SELECT * FROM {self.table_name}"
		records = await self._fetch_all(query)
		return await self._records_to_models(records)

	async def delete(self, channel_id: int) -> None:
		"""Удаление канала"""
		query = f"DELETE FROM {self.table_name} WHERE channel_id = $1"
		await self._execute(query, channel_id)

	async def count_channels(self) -> int:
		async with self.pool.acquire() as conn:
			return await conn.fetchval(
				f"SELECT COUNT(*) FROM {self.table_name}"
			)
