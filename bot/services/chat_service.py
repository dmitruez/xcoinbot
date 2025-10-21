import html
from typing import List

from aiogram import Bot

from ..keyboards.admin_keyboard import AdminKeyboards
from ..models import ChatMessage, ChatDialog, User
from ..repositories import ChatRepository, AdminRepository, UserRepository
from ..utils.loggers import services as logger


class ChatService:
	"""Сервис для общения админов и пользователей"""

	def __init__(
		self,
		bot: Bot,
		chat_repo: ChatRepository,
		admin_repo: AdminRepository,
		user_repo: UserRepository
	):
		self.bot = bot
		self.chat_repo = chat_repo
		self.admin_repo = admin_repo
		self.user_repo = user_repo

	async def save_user_message(self, user_id: int, text: str) -> ChatMessage | None:
		try:
			return await self.chat_repo.add_message(
				user_id=user_id,
				sender='user',
				message=text,
				is_read=False
			)
		except Exception as e:
			logger.error(f"Ошибка сохранения сообщения пользователя {user_id}: {e}")
			return None

	async def save_admin_message(self, admin_id: int, user_id: int, text: str) -> ChatMessage | None:
		try:
			return await self.chat_repo.add_message(
				user_id=user_id,
				sender='admin',
				message=text,
				admin_id=admin_id,
				is_read=True
			)
		except Exception as e:
			logger.error(f"Ошибка сохранения сообщения админа {admin_id} пользователю {user_id}: {e}")
			return None

	async def mark_read(self, user_id: int) -> None:
		try:
			await self.chat_repo.mark_read(user_id)
		except Exception as e:
			logger.error(f"Ошибка отметки прочитанным диалога {user_id}: {e}")

	async def get_history(self, user_id: int, limit: int = 30) -> List[ChatMessage]:
		try:
			history = await self.chat_repo.get_history(user_id, limit)
			return list(reversed(history))
		except Exception as e:
			logger.error(f"Ошибка получения истории диалога {user_id}: {e}")
			return []

	async def get_unread_dialogs(self, limit: int = 15) -> List[ChatDialog]:
		try:
			records = await self.chat_repo.get_unread_dialogs(limit)
			return await self._records_to_dialogs(records)
		except Exception as e:
			logger.error(f"Ошибка получения непрочитанных диалогов: {e}")
			return []

	async def get_recent_dialogs(self, limit: int = 15) -> List[ChatDialog]:
		try:
			records = await self.chat_repo.get_recent_dialogs(limit)
			return await self._records_to_dialogs(records)
		except Exception as e:
			logger.error(f"Ошибка получения последних диалогов: {e}")
			return []

	async def _records_to_dialogs(self, records) -> List[ChatDialog]:
		dialogs: List[ChatDialog] = []
		for record in records:
			user = await self.user_repo.get_by_id(record['user_id'])
			full_name = user.full_name if user else 'Без имени'
			username = user.username if user else None
			unread = record['unread_count'] if 'unread_count' in record else 0
			dialogs.append(ChatDialog(
				user_id=record['user_id'],
				full_name=full_name,
				username=username,
				last_message=record['message'],
				last_sender=record['sender'],
				last_at=record['created_at'],
				unread_count=unread
			))
		return dialogs

	async def notify_admins_about_user_message(self, user: User, text: str) -> None:
		try:
			admins = await self.admin_repo.get_all()
			if not admins:
				return

			escaped_text = html.escape(text)
			user_name = html.escape(user.full_name)

			for admin in admins:
				if admin.user_id == user.user_id:
					continue
				try:
					await self.bot.send_message(
						admin.user_id,
						(
							"📩 <b>Новое сообщение от пользователя</b>\n\n"
							+ f"Имя: {user_name}\n"
							+ f"ID: <code>{user.user_id}</code>\n\n"
							+ f"<code>{escaped_text}</code>"
						),
						reply_markup=AdminKeyboards.chat_notification(user.user_id)
					)
				except Exception as send_error:
					logger.error(f"Ошибка отправки уведомления админу {admin.user_id}: {send_error}")
		except Exception as e:
			logger.error(f"Ошибка уведомления админов о сообщении пользователя {user.user_id}: {e}")

	async def send_reply(self, admin_id: int, user_id: int, text: str) -> bool:
		saved = await self.save_admin_message(admin_id, user_id, text)
		if not saved:
			return False

		try:
			await self.bot.send_message(
				user_id,
				"📨 <b>Сообщение от администрации</b>\n\n" + html.escape(text)
			)
			return True
		except Exception as e:
			logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
			return False