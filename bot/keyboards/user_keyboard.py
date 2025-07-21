from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class UserKeyboards:
	@staticmethod
	def captcha_refresh():
		"""Клавиатура для обновления капчи"""
		builder = InlineKeyboardBuilder()
		builder.add(InlineKeyboardButton(
			text="🔄 Обновить капчу",
			callback_data="refresh_captcha"
		))
		return builder.as_markup()
