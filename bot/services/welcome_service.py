import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, types
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models import Channel
from ..repositories import Repositories
from ..utils.loggers import services as logger


class WelcomeService:
	TEMPLATE_FILE = "welcome_template.json"
	
	def __init__(self, bot: Bot, repos: Repositories):
		self.bot = bot
		self.repos = repos
		self.template = self.load_template()
	
	def load_template(self) -> Dict:
		"""Загрузка шаблона из JSON-файла"""
		if not Path(self.TEMPLATE_FILE).exists():
			# Создаем дефолтный шаблон
			default_template = {
				"text": "👋 Добро пожаловать!\n\nМы рады видеть вас в нашем сообществе.",
				"media_type": None,
				"media_file_id": None,
				"buttons": []
			}
			self.save_template(template=default_template)
			return default_template
		
		try:
			with open(self.TEMPLATE_FILE, 'r', encoding='utf-8') as f:
				return json.load(f)
		except Exception as e:
			logger.error(f"Ошибка загрузки шаблона приветствия: {e}")
			return {
				"text": "",
				"media_type": None,
				"media_file_id": None,
				"buttons": []
			}
	
	def save_template(self, template: Dict = None) -> None:
		"""Сохранение шаблона в JSON-файл"""
		data = template or self.template
		with open(self.TEMPLATE_FILE, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
	
	async def get_welcome_data(self) -> Dict:
		"""Получение текущего шаблона приветствия"""
		return self.template
	
	async def update_text(self, new_text: str) -> None:
		"""Обновление текста приветствия"""
		self.template["text"] = new_text
		self.save_template()
	
	async def update_media(self, media_type: str, file_id: str) -> None:
		"""Обновление медиа-контента"""
		self.template["media_type"] = media_type
		self.template["media_file_id"] = file_id
		self.save_template()
	
	async def remove_media(self) -> None:
		"""Удаление медиа-контента"""
		self.template["media_type"] = None
		self.template["media_file_id"] = None
		self.save_template()
	
	async def add_button(
			self,
			button_text: str,
			button_type: str,
			button_value: str
	) -> bool:
		"""Добавление кнопки с указанием типа"""
		if len(self.template["buttons"]) >= 5:
			return False
		
		button_id = str(uuid.uuid4())
		
		self.template["buttons"].append({
			'id': button_id,
			"text": button_text,
			"type": button_type,
			"value": button_value
		})
		self.save_template()
		return True
	
	async def get_button_by_id(self, button_id: str) -> Optional[dict]:
		"""Поиск кнопки по ID"""
		for btn in self.template["buttons"]:
			if btn.get("id") == button_id:
				return btn
		return None
	
	async def clear_buttons(self) -> None:
		"""Очистка всех кнопок шаблона"""
		self.template["buttons"] = []
		self.save_template()
	
	async def remove_button(self, index: int) -> bool:
		"""Удаление кнопки по индексу"""
		if 0 <= index < len(self.template["buttons"]):
			self.template["buttons"].pop(index)
			self.save_template()
			return True
		return False
	
	async def format_welcome(self) -> Tuple[str, Optional[str], Optional[str], Optional[types.InlineKeyboardMarkup]]:
		"""Форматирование приветственного сообщения"""
		template = self.load_template()
		text = template["text"]
		media_type = template["media_type"]
		media_file_id = template["media_file_id"]
		buttons = template["buttons"]
		
		keyboard = None
		if buttons:
			builder = InlineKeyboardBuilder()
			for btn in buttons:
				if btn['type'] == 'url':
					builder.button(text=btn["text"], url=btn["value"])
				else:
					builder.button(text=btn["text"], callback_data=f"welcome_textbtn:{btn['id']}")
			builder.adjust(1)  # 1 кнопка в ряд
			keyboard = builder.as_markup()
		
		return text, media_type, media_file_id, keyboard
	
	
	async def send_welcome(self, user_id: int, channel: Channel) -> bool:
		"""Отправка приветственного сообщения пользователю"""
		try:
			text, media_type, media_file_id, keyboard = await self.format_welcome()
			
			text = text.replace('&link', channel.link)
			text = text.replace('&title', channel.title)
			
			if media_type and media_file_id:
				# Отправка медиа с текстом
				if media_type == "photo":
					await self.bot.send_photo(
						chat_id=user_id,
						photo=media_file_id,
						caption=text,
						reply_markup=keyboard
					)
				elif media_type == "video":
					await self.bot.send_video(
						chat_id=user_id,
						video=media_file_id,
						caption=text,
						reply_markup=keyboard
					)
				elif media_type == "animation":
					await self.bot.send_animation(
						chat_id=user_id,
						animation=media_file_id,
						caption=text,
						reply_markup=keyboard
					)
				elif media_type == "document":
					await self.bot.send_document(
						chat_id=user_id,
						document=media_file_id,
						caption=text,
						reply_markup=keyboard
					)
				return True
			else:
				# Отправка только текста
				await self.bot.send_message(
					chat_id=user_id,
					text=text,
					reply_markup=keyboard
				)
				return True
		except Exception as e:
			logger.error(f"Ошибка отправки приветствия пользователю {user_id}: {e}")
			return False