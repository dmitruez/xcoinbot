# Система уведомлений
import json
from pathlib import Path
from typing import Dict, Optional

from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .message_service import MessageService
from ..models import MessageTemplate, Channel, Button
from ..repositories import Repositories
from ..utils.loggers import services as logger


class NotificationService(MessageService):
	TEMPLATE_FILE = "notification_template.json"

	def __init__(self, bot: Bot, repos: Repositories):
		super().__init__(bot, repos, 'notif', '🔔 Основной канал изменен!\n\nНовый канал: &title \nСсылка: &link')

	async def notify_channel_change(self, channel: Channel) -> Dict[str, int]:
		"""Отправка уведомлений о смене канала"""
		users = await self.repos.user.get_users_for_notification()
		text, media_type, media_id, buttons = await self.format_message(channel)
		keyboard = await self.format_keyboard(buttons)
		
		text = text.replace('&link', channel.link)
		text = text.replace('&title', channel.title)

		success = 0
		failures = 0

		for user in users:
			try:
				await self.send_message(user.user_id, text, media_type, media_id, keyboard)
				await self.bot.send_message(
					chat_id=user.user_id,
					text=text,
					reply_markup=keyboard if keyboard else None,
					disable_web_page_preview=True
				)
				success += 1
			except Exception as e:
				logger.error(f"Failed to notify user {user.user_id}: {e}")
				failures += 1
				await self.repos.user.set_notification_status(user.user_id, False)
				await self.repos.user.ban_user(user.user_id)

		return {'success': success, 'failures': failures}
