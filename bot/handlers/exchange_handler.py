from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from .captcha_handler import send_captcha
from ..keyboards.exchange_keyboards import ExchangeKeyboards
from ..keyboards.user_keyboard import UserKeyboards
from ..services import Services
from ..states.exchange_states import ExchangeStates


router = Router(name=__name__)


@router.message(F.data == "exchange")
async def start_exchange(message: Message, state: FSMContext):
	"""Начало процесса обмена"""

	await message.answer(
		"Выберите способ оплаты:",
		reply_markup=ExchangeKeyboards.payment_methods()
	)
	await state.set_state(ExchangeStates.SELECT_PAYMENT_METHOD)


@router.callback_query(F.data.startswith("method_"), ExchangeStates.SELECT_PAYMENT_METHOD)
async def select_payment_method(callback: CallbackQuery, state: FSMContext):
	"""Выбор способа оплаты"""

	method = callback.data.split("_")[1]
	await state.update_data(payment_method=method)

	await callback.message.edit_text(
		"Выберите валютную пару:",
		reply_markup=ExchangeKeyboards.currency_pairs()
	)
	await state.set_state(ExchangeStates.SELECT_CURRENCY_PAIR)


@router.callback_query(F.data.startswith("pair_"), ExchangeStates.SELECT_CURRENCY_PAIR)
async def select_currency_pair(callback: CallbackQuery, state: FSMContext, services: Services):
	"""Выбор валютной пары и получение курсов"""
	currency_pair = callback.data.split("_")[1]
	from_curr, to_curr = currency_pair.split("-")

	await state.update_data(currency_pair=currency_pair, from_curr=from_curr, to_curr=to_curr)

	# Получаем курсы от бирж
	rates = await services.exchange.get_rates(from_curr, to_curr)

	if not rates:
		await callback.answer("❌ Нет доступных курсов, попробуйте позже", show_alert=True)
		return

	await state.update_data(rates=rates)

	# Формируем сообщение с курсами
	text = "🔍 Доступные курсы:\n\n"
	for exchange, rate in rates.items():
		text += f"• {exchange.capitalize()}: 1 {from_curr} = {rate} {to_curr}\n"

	await callback.message.edit_text(
		text,
		reply_markup=ExchangeKeyboards.exchanges_list(list(rates.keys()))
	)
	await state.set_state(ExchangeStates.SELECT_EXCHANGE)


@router.callback_query(F.data.startswith("exchange_"))
async def select_exchange(callback: CallbackQuery, state: FSMContext):
	"""Выбор обменника"""
	exchange = callback.data.split("_")[1]
	await state.update_data(selected_exchange=exchange)

	data = await state.get_data()
	rate = data['rates'][exchange]

	await callback.message.edit_text(
		f"Вы выбрали: {exchange.capitalize()}\n"
		f"Курс: 1 {data['from_curr']} = {rate} {data['to_curr']}\n\n"
		f"Введите сумму для обмена в {data['from_curr']}:"
	)
	await state.set_state(ExchangeStates.INPUT_AMOUNT)


@router.message(F.text, ExchangeStates.INPUT_AMOUNT)
async def input_amount(message: Message, state: FSMContext):
	"""Обработка ввода суммы"""
	try:
		amount = float(message.text)
		if amount <= 0:
			raise ValueError
	except ValueError:
		await message.answer("❌ Неверная сумма. Введите число больше 0:")
		return

	await state.update_data(amount=amount)

	# Рассчитываем итоговую сумму
	data = await state.get_data()
	rate = data['rates'][data['selected_exchange']]
	total = amount * rate

	await message.answer(
		f"Сумма к получению: {total:.2f} {data['to_curr']}\n\n"
		"Введите ваши реквизиты для получения средств:",
		reply_markup=ExchangeKeyboards.cancel_exchange()
	)
	await state.set_state(ExchangeStates.INPUT_USER_DATA)


@router.message(ExchangeStates.INPUT_USER_DATA)
async def input_user_data(message: Message, state: FSMContext, services: Services):
	"""Обработка ввода реквизитов"""
	user_id = message.from_user.id
	await state.update_data(recipient_data=message.text)

	# Генерируем и отправляем капчу
	captcha_text, image_path = await services.captcha.generate_captcha(user_id)

	# Отправляем капчу как файл
	captcha_message = await message.answer_photo(
		photo=FSInputFile(image_path),
		caption="Введите текст с изображения:",
		reply_markup=UserKeyboards.captcha_refresh()
	)
	# Удаляем файл после отправки
	await services.captcha.cleanup(image_path)
	await state.update_data(captcha_message=captcha_message, attemps=0)
	await state.set_state(ExchangeStates.CAPTCHA)


@router.message(ExchangeStates.CAPTCHA)
async def check_captcha(message: Message, state: FSMContext, services: Services):
	"""Проверка капчи и вывод условий"""
	if len(message.text) > 6:
		return
	await message.delete()
	user_id = message.from_user.id
	user_input = message.text.strip()

	# Проверяем капчу
	success, response, attemps = await services.captcha.verify_captcha(user_id, user_input)

	# Очищаем временный файл капчи
	state_data = await state.get_data()
	captcha_message: Message = state_data["captcha_message"]


	if not success:
		await message.answer("❌ Неверная капча! Попробуйте еще раз:")
		return

	# Формируем условия обмена
	# terms = (
	# 	f"<b>Детали заявки:</b>\n\n"
	# 	f"• Обменник: {data['selected_exchange'].capitalize()}\n"
	# 	f"• Направление: {data['from_curr']} → {data['to_curr']}\n"
	# 	f"• Сумма: {data['amount']} {data['from_curr']}\n"
	# 	f"• К получению: {data['amount'] * data['rates'][data['selected_exchange']]} {data['to_curr']}\n"
	# 	f"• Реквизиты: {data['recipient_data']}\n\n"
	# 	"<b>Условия:</b>\n"
	# 	"1. Обмен производится в течение 15 минут\n"
	# 	"2. Комиссия сети оплачивается отправителем\n"
	# 	"3. Курс фиксируется на момент создания заявки"
	# )

	# await message.answer(
	# 	terms,
	# 	parse_mode="HTML",
	# 	reply_markup=ExchangeKeyboards.terms_agreement()
	# )
	# await state.set_state(ExchangeStates.TERMS_AGREEMENT)