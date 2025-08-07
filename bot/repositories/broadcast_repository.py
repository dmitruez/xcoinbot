import asyncpg
import json
from datetime import datetime
from typing import List, Optional, Dict, Tuple

from .base_repository import BaseRepository
from ..models import BroadcastMessage, Button


class BroadcastRepository(BaseRepository[BroadcastMessage]):
	def __init__(self, pool: asyncpg.Pool):
		super().__init__(pool, 'broadcasts', BroadcastMessage)
	
	async def create_table(self) -> None:
		"""Создание таблицы рассылок"""
		query = """
        CREATE TABLE IF NOT EXISTS broadcasts (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            media_type TEXT NOT NULL,
            media_id TEXT,
            buttons JSONB NOT NULL DEFAULT '[]'::jsonb,
            sent_at TIMESTAMP NOT NULL,
            sent_by BIGINT NOT NULL,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            total_users INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_broadcasts_sent_at ON broadcasts(sent_at);
        CREATE INDEX IF NOT EXISTS idx_broadcasts_sent_by ON broadcasts(sent_by);
        """
		await self._execute(query)
	
	async def create(self, broadcast: BroadcastMessage) -> int:
		"""Создание новой записи о рассылке"""
		query = f"""
        INSERT INTO {self.table_name}
        (text, media_type, media_id, buttons, sent_at, sent_by,
         success_count, error_count, total_users)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """
		buttons_json = json.dumps([
			btn.__dict__
			for btn in broadcast.buttons
		])
		
		async with self.pool.acquire() as conn:
			record = await conn.fetchrow(
				query,
				broadcast.text,
				broadcast.media_type,
				broadcast.media_id,
				buttons_json,
				broadcast.sent_at,
				broadcast.sent_by,
				broadcast.success_count,
				broadcast.error_count,
				broadcast.total_users
			)
		return record['id'] if record else None
	
	async def update_stats(self, broadcast_id: int, success: int, errors: int) -> None:
		"""Обновление статистики рассылки"""
		query = f"""
        UPDATE {self.table_name} SET
            success_count = success_count + $2,
            error_count = error_count + $3
        WHERE id = $1
        """
		await self._execute(query, broadcast_id, success, errors)
	
	async def get_by_id(self, broadcast_id: int) -> Optional[BroadcastMessage]:
		"""Получение рассылки по ID"""
		query = f"SELECT * FROM {self.table_name} WHERE id = $1"
		record = await self._fetch(query, broadcast_id)
		return await self._record_to_model(record)
	
	async def get_history(self, limit: int = 10) -> List[BroadcastMessage]:
		"""Получение истории рассылок"""
		query = f"SELECT * FROM {self.table_name} ORDER BY sent_at DESC LIMIT $1"
		records = await self._fetch_all(query, limit)
		return await self._records_to_models(records)
	
	async def _record_to_model(self, record: Optional[asyncpg.Record]) -> Optional[BroadcastMessage]:
		"""Преобразование записи БД в модель"""
		if not record:
			return None
		
		# Преобразование JSON кнопок
		buttons = []
		if record['buttons']:
			buttons = [
				Button(**btn)
				for btn in json.loads(record['buttons'])
			]
		
		return BroadcastMessage(
			id=record['id'],
			text=record['text'],
			media_type=record['media_type'],
			media_id=record['media_id'],
			buttons=buttons,
			sent_at=record['sent_at'],
			sent_by=record['sent_by'],
			success_count=record['success_count'],
			error_count=record['error_count'],
			total_users=record['total_users']
		)
	
	async def _records_to_models(self, records: List[asyncpg.Record]) -> List[BroadcastMessage]:
		"""Преобразование списка записей в список моделей"""
		return [await self._record_to_model(record) for record in records]