# Система уведомлений

from typing import List, Dict, Optional
from aiogram import Bot, types
from aiogram.utils.markdown import code
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ..models import NotificationTemplate
from ..repositories import Repositories
from ..utils.loggers import services as logger

class NotificationService:
	def __init__(self, bot: Bot, repos: Repositories):
		self.bot = bot
		self.repos = repos
		self.template = NotificationTemplate(
			text="🔔 Основной канал изменен!\n\n"
				 "Новый канал: {channel_title}\n"
				 "Ссылка: {channel_link}",
			buttons=[]
		)

	async def get_template(self) -> NotificationTemplate:
		"""Получение текущего шаблона уведомления"""
		return self.template

	async def update_template_text(self, new_text: str) -> None:
		"""Обновление текста шаблона"""
		self.template.text = new_text

	async def add_template_button(self, text: str, url: str) -> None:
		"""Добавление кнопки к шаблону"""
		self.template.buttons.append((text, url))

	async def clear_template_buttons(self) -> None:
		"""Очистка всех кнопок шаблона"""
		self.template.buttons.clear()

	async def format_notification(self, channel) -> tuple[str, Optional[types.InlineKeyboardMarkup]]:
		"""Форматирование уведомления по шаблону"""
		channel_link = f"https://t.me/{channel.username}" if channel.username \
			else f"https://t.me/c/{str(channel.id)[4:]}"

		formatted_text = self.template.text.format(
			channel_title=code(channel.title),
			channel_link=code(channel_link)
		)

		keyboard = None
		if self.template.buttons:
			keyboard = InlineKeyboardBuilder()
			for text, url in self.template.buttons:
				keyboard.button(text=text, url=url)

		return formatted_text, keyboard

	async def notify_channel_change(self, new_channel_id: int) -> Dict[str, int]:
		"""Отправка уведомлений о смене канала"""
		new_channel = await self.repos.channel.get(new_channel_id)
		if not new_channel:
			return {'success': 0, 'failures': 0}

		users = await self.repos.user.get_all_should_notify()
		text, keyboard = await self.format_notification(new_channel)

		success = 0
		failures = 0

		for user in users:
			try:
				await self.bot.send_message(
					chat_id=user.id,
					text=text,
					reply_markup=keyboard,
					disable_web_page_preview=True
				)
				success += 1
			except Exception as e:
				logger.error(f"Failed to notify user {user.id}: {e}")
				failures += 1
				await self.repos.user.set_notification_status(user.id, False)

		return {'success': success, 'failures': failures}