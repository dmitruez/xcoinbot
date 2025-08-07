import json
import uuid
from pathlib import Path
from typing import Optional, Tuple, Generic, TypeVar, List

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models import MessageTemplate, Button, Channel
from ..repositories import Repositories
from ..utils.loggers import services as logger



class MessageService:
	TEMPLATE_FILE = None
	
	def __init__(self, bot: Bot, repos: Repositories, callback: str, default_text: str):
		self.bot = bot
		self.repos = repos
		self.callback = callback
		self.default_text = default_text
		self.template = self.load_template()
		
		
	def load_template(self) -> MessageTemplate:
		"""Загрузка шаблона из JSON-файла"""
		if not Path(self.TEMPLATE_FILE).exists():
			# Создаем дефолтный шаблон
			default_template = MessageTemplate(
				text=self.default_text,
				media_id=None,
				media_type=None,
				buttons=[]
			)
			self.save_template(template=default_template)
			return default_template
		
		try:
			with open(self.TEMPLATE_FILE, 'r', encoding='utf-8') as f:
				data = json.load(f)
				return MessageTemplate(
					text=data['text'],
					media_id=data['media_id'],
					media_type=data['media_type'],
					buttons=[Button(**button) for button in data['buttons']]
				)
		except Exception as e:
			logger.error(f"Ошибка загрузки шаблона: {e}")
			return MessageTemplate(text="", media_id=None, media_type=None, buttons=[])
		
	def save_template(self, template: MessageTemplate = None) -> None:
		"""Сохранение шаблона в JSON-файл"""
		temp = template or self.template
		data = {
			"text": temp.text,
			"media_id": temp.media_id,
			"media_type": temp.media_type,
			"buttons": [button.__dict__ for button in temp.buttons] if temp.buttons else []
		}
		with open(self.TEMPLATE_FILE, 'w', encoding='utf-8') as f:
			json.dump(data, f, ensure_ascii=False, indent=2)
			
			
	async def get_template(self) -> MessageTemplate:
		"""Получение текущего шаблона"""
		return self.template
	
	
	async def update_text(self, new_text: str) -> None:
		"""Обновление текста шаблона"""
		self.template.text = new_text
		self.save_template()
		
	
	async def update_media(self, media_type: str, file_id: str) -> None:
		"""Обновление медиа-контента"""
		self.template.media_type = media_type
		self.template.media_id = file_id
		self.save_template()
		
	async def remove_media(self) -> None:
		"""Удаление медиа-контента"""
		self.template.media_type = None
		self.template.media_file_id = None
		self.save_template()
	
	async def add_button(self, button_text: str, button_type: str, button_value: str) -> bool:
		"""Добавление кнопки с указанием типа"""
		if len(self.template.buttons) >= 5:
			return False
		
		button_id = str(uuid.uuid4())
		
		self.template.buttons.append(Button(
			id=button_id,
			text=button_text,
			button_type=button_type,
			value=button_value
		))
		self.save_template()
		return True
	
	async def get_button_by_id(self, button_id: str) -> Optional[Button]:
		"""Поиск кнопки по ID"""
		for btn in self.template.buttons:
			if btn.id == button_id:
				return btn
		return None
	
	async def clear_buttons(self) -> None:
		"""Очистка всех кнопок шаблона"""
		self.template.buttons = []
		self.save_template()
		
	async def remove_button(self, index: int) -> bool:
		"""Удаление кнопки по индексу"""
		if 0 <= index < len(self.template.buttons):
			self.template.buttons.pop(index)
			self.save_template()
			return True
		return False
	
	async def format_message(self, channel: Channel) -> Tuple[str, str, str, List[Button]]:
		"""Форматирование приветственного сообщения"""
		template = self.load_template()
		text = template.text
		text = text.replace('&link', channel.link)
		text = text.replace('&title', channel.title)
		
		media_type = template.media_type
		media_id = template.media_id
		buttons = template.buttons
		
		return text, media_type, media_id, buttons
	
	
	async def format_keyboard(self, buttons: List[Button]) -> Optional[InlineKeyboardMarkup]:
		keyboard = None
		if buttons:
			builder = InlineKeyboardBuilder()
			for btn in buttons:
				if btn.button_type == 'url':
					builder.button(text=btn.text, url=btn.value)
				else:
					builder.button(text=btn.text, callback_data=f"{self.callback}_textbtn:{btn.id}")
			builder.adjust(1)  # 1 кнопка в ряд
			keyboard = builder.as_markup()
		return keyboard
	
	async def send_message(self, user_id: int, text: str, media_type: str, media_id: str, keyboard: Optional[InlineKeyboardMarkup]) -> Optional[Message]:
		"""Отправка приветственного сообщения пользователю"""
		try:
			if media_type and media_id:
				# Отправка медиа с текстом
				if media_type == "photo":
					message = await self.bot.send_photo(
						chat_id=user_id,
						photo=media_id,
						caption=text,
						reply_markup=keyboard
					)
				elif media_type == "video":
					message = await self.bot.send_video(
						chat_id=user_id,
						video=media_id,
						caption=text,
						reply_markup=keyboard
					)
				elif media_type == "animation":
					message = await self.bot.send_animation(
						chat_id=user_id,
						animation=media_id,
						caption=text,
						reply_markup=keyboard
					)
				else:
					message = await self.bot.send_message(
						chat_id=user_id,
						text=text,
						reply_markup=keyboard
					)
				return message
			else:
				# Отправка только текста
				message = await self.bot.send_message(
					chat_id=user_id,
					text=text,
					reply_markup=keyboard
				)
				return message
		except Exception as e:
			logger.exception(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
			return False