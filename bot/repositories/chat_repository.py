from typing import List, Optional

import asyncpg

from .base_repository import BaseRepository
from ..models import ChatMessage


class ChatRepository(BaseRepository[ChatMessage]):

	def __init__(self, pool: asyncpg.Pool):
		super().__init__(pool, 'chat_messages', ChatMessage)

	async def create_table(self) -> None:
		"""Создание таблицы для сообщений"""
		query = """
		CREATE TABLE IF NOT EXISTS chat_messages (
			id SERIAL PRIMARY KEY,
			user_id BIGINT NOT NULL,
			sender TEXT NOT NULL CHECK (sender IN ('user', 'admin')),
			message TEXT NOT NULL,
			created_at TIMESTAMP DEFAULT NOW(),
			is_read BOOLEAN DEFAULT FALSE,
			admin_id BIGINT DEFAULT NULL
		);
		CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id);
		CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
		CREATE INDEX IF NOT EXISTS idx_chat_messages_unread ON chat_messages(user_id, is_read) WHERE sender = 'user';
		"""
		await self._execute(query)

	async def add_message(
		self,
		user_id: int,
		sender: str,
		message: str,
		admin_id: Optional[int] = None,
		is_read: bool = False
	) -> ChatMessage:
		query = f"""
		INSERT INTO {self.table_name} (user_id, sender, message, admin_id, is_read)
		VALUES ($1, $2, $3, $4, $5)
		RETURNING *
		"""
		record = await self._fetch(query, user_id, sender, message, admin_id, is_read)
		return await self._record_to_model(record)

	async def get_history(self, user_id: int, limit: int = 30) -> List[ChatMessage]:
		query = f"""
		SELECT * FROM {self.table_name}
		WHERE user_id = $1
		ORDER BY created_at DESC
		LIMIT $2
		"""
		records = await self._fetch_all(query, user_id, limit)
		return await self._records_to_models(records)

	async def mark_read(self, user_id: int) -> None:
		query = f"""
		UPDATE {self.table_name}
		SET is_read = TRUE
		WHERE user_id = $1 AND sender = 'user' AND is_read = FALSE
		"""
		await self._execute(query, user_id)

	async def get_unread_dialogs(self, limit: int = 15) -> List[asyncpg.Record]:
		query = f"""
		WITH ranked AS (
			SELECT
				cm.*,
				ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
			FROM {self.table_name} cm
		), unread AS (
			SELECT user_id, COUNT(*) AS unread_count
			FROM {self.table_name}
			WHERE sender = 'user' AND is_read = FALSE
			GROUP BY user_id
		)
		SELECT
			r.user_id,
			r.message,
			r.sender,
			r.created_at,
			u.unread_count
		FROM ranked r
		JOIN unread u ON r.user_id = u.user_id
		WHERE r.rn = 1
		ORDER BY r.created_at DESC
		LIMIT $1
		"""
		return await self._fetch_all(query, limit)

	async def get_recent_dialogs(self, limit: int = 15) -> List[asyncpg.Record]:
		query = f"""
		SELECT user_id, message, sender, created_at
		FROM (
			SELECT
				cm.*,
				ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
			FROM {self.table_name} cm
		) ranked
		WHERE rn = 1
		ORDER BY created_at DESC
		LIMIT $1
		"""
		return await self._fetch_all(query, limit)
