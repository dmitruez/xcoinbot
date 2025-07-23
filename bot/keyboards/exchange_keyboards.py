from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, KeyboardButton


class ExchangeKeyboards:
	@staticmethod
	def payment_methods():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="💳 Банковская карта", callback_data="method_card"),
			InlineKeyboardButton(text="📱 Электронные кошельки", callback_data="method_electronic"),
			InlineKeyboardButton(text="₿ Криптовалюта", callback_data="method_crypto"),
			InlineKeyboardButton(text="🏦 SEPA/Bank Transfer", callback_data="method_bank"),
			InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_exchange")
		)
		builder.adjust(2)
		return builder.as_markup()

	@staticmethod
	def currency_pairs():
		builder = InlineKeyboardBuilder()
		popular_pairs = [
			("BTC/USDT", "BTC-USDT"),
			("ETH/USDT", "ETH-USDT"),
			("USDT/RUB", "USDT-RUB"),
			("BTC/ETH", "BTC-ETH"),
			("USDT/EUR", "USDT-EUR"),
			("ETH/BTC", "ETH-BTC")
		]
		for text, data in popular_pairs:
			builder.add(InlineKeyboardButton(text=text, callback_data=f"pair_{data}"))
		builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_exchange"))
		builder.adjust(2)
		return builder.as_markup()

	@staticmethod
	def exchanges_list(exchanges):
		builder = InlineKeyboardBuilder()
		for exchange in exchanges:
			builder.add(InlineKeyboardButton(
				text=exchange.capitalize(),
				callback_data=f"exchange_{exchange}"
			))
		builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_exchange"))
		builder.adjust(2)
		return builder.as_markup()

	@staticmethod
	def terms_agreement():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="✅ Согласен с условиями", callback_data="agree_terms"),
			InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_exchange")
		)
		return builder.as_markup()

	@staticmethod
	def cancel_exchange():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_exchange")
		)
		return builder.as_markup()
