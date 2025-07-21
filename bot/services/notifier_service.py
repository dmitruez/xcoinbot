# Система уведомлений
import json
from pathlib import Path
from typing import Dict, Optional

from aiogram import Bot, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models import NotificationTemplate, Channel
from ..repositories import Repositories
from ..utils.loggers import services as logger


class NotificationService:
	TEMPLATE_FILE = "notification_template.json"

	def __init__(self, bot: Bot, repos: Repositories):
		self.bot = bot
		self.repos = repos
		self.template = self.load_template()

	def load_template(self) -> NotificationTemplate:
		"""Загрузка шаблона из JSON-файла"""
		if not Path(self.TEMPLATE_FILE).exists():
			# Создаем дефолтный шаблон
			default_template = NotificationTemplate(
				text="🔔 Основной канал изменен!\n\nНовый канал: &title \nСсылка: &link",
				buttons=[]
			)
			self.save_template(template=default_template)
			return default_template

		try:
			with open(self.TEMPLATE_FILE, 'r', encoding='utf-8') as f:
				data = json.load(f)
				return NotificationTemplate(
					text=data['text'],
					buttons=[(btn['text'], btn['url']) for btn in data['buttons']]
				)
		except Exception as e:
			logger.error(f"Ошибка загрузки шаблона: {e}")
			return NotificationTemplate(text="", buttons=[])

	def save_template(self, template: NotificationTemplate = None) -> None:
		"""Сохранение шаблона в JSON-файл"""
		if template:
			data = {
				"text": template.text,
				"buttons": [{"text": text, "url": url} for text, url in template.buttons]
			}
		else:
			data = {
				"text": self.template.text,
				"buttons": [{"text": text, "url": url} for text, url in self.template.buttons]
			}

		with open(self.TEMPLATE_FILE, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)

	async def get_template(self) -> NotificationTemplate:
		"""Получение текущего шаблона"""
		return self.template

	async def update_template_text(self, new_text: str) -> None:
		"""Обновление текста шаблона"""
		self.template.text = new_text
		self.save_template()

	async def add_template_button(self, text: str, url: str) -> bool:
		"""Добавление кнопки к шаблону"""
		if len(self.template.buttons) >= 5:  # Ограничение на количество кнопок
			return False
		self.template.buttons.append((text, url))
		self.save_template()
		return True

	async def clear_template_buttons(self) -> None:
		"""Очистка всех кнопок шаблона"""
		self.template.buttons.clear()
		self.save_template()

	async def remove_template_button(self, index: int) -> bool:
		"""Удаление кнопки по индексу"""
		if 0 <= index < len(self.template.buttons):
			self.template.buttons.pop(index)
			self.save_template()
			return True
		return False

	async def format_notification(self, channel) -> tuple[str, Optional[types.InlineKeyboardMarkup]]:
		"""Форматирование уведомления по шаблону"""

		formatted_text = self.template.text
		formatted_text = formatted_text.replace("&title", channel.title)
		formatted_text = formatted_text.replace("&link", channel.link)

		keyboard = None
		if self.template.buttons:
			builder = InlineKeyboardBuilder()
			for text, url in self.template.buttons:
				builder.button(text=text, url=url)
			builder.adjust(1)  # 1 кнопка в ряд
			keyboard = builder.as_markup()

		return formatted_text, keyboard

	async def notify_channel_change(self, new_channel: Channel) -> Dict[str, int]:
		"""Отправка уведомлений о смене канала"""
		users = await self.repos.user.get_users_for_notification()
		text, keyboard = await self.format_notification(new_channel)

		success = 0
		failures = 0

		for user in users:
			try:
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

		return {'success': success, 'failures': failures}
