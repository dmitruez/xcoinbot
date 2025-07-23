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


	@staticmethod
	def exchange_direction():
		"""Клавиатура для выбора направления обмена"""
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="BTC → USDT", callback_data="btc_usdt"),
			InlineKeyboardButton(text="USDT → RUB", callback_data="usdt_rub")
		)
		return builder.as_markup()