from datetime import datetime

from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ...keyboards.admin_keyboard import AdminKeyboards
from ...services import Services
from ...states.admin_states import StatsStates


router = Router(name=__name__)


@router.message(Command('stats'))
async def redirect_admin_stats(message: types.Message, services: Services):
	await admin_stats(message, services)




@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery | types.Message, services: Services):
	"""Статистика бота"""
	stats = await services.admin.get_stats()

	text = (
		"📊 <b>Статистика бота</b>\n\n"
		f"👤 Всего пользователей: <code>{stats['total_users']}</code>\n"
		f"🟢 Активных: <code>{stats['active_users']}</code>\n"
		f"🔴 Заблокированных: <code>{stats['banned_users']}</code>\n\n"
		f"📢 Каналов: <code>{stats['channels_count']}</code>\n"
		f"🔷 Основной: {stats['main_channel']}\n"
		f"🔶 Резервный: {stats['backup_channel']}"
	)

	if isinstance(callback, types.CallbackQuery):
		await callback.message.edit_text(
			text,
			reply_markup=AdminKeyboards.back_to_main()
		)
		await callback.answer()
	else:
		await callback.answer(
			text,
			reply_markup=AdminKeyboards.back_to_main()
		)


@router.callback_query(F.data == "admin_stats_period")
async def request_stats_period(callback: types.CallbackQuery, state: FSMContext):
	"""Запрос периода для статистики"""
	await callback.message.edit_text(
		"📅 <b>Статистика за период</b>\n\n"
		"Введите начальную дату в формате ГГГГ-ММ-ДД:",

		reply_markup=AdminKeyboards.back_to_main()
	)
	await state.set_state(StatsStates.WAITING_START_DATE)
	await callback.answer()


@router.message(StatsStates.WAITING_START_DATE)
async def process_start_date(message: types.Message, state: FSMContext):
	"""Обработка начальной даты"""
	try:
		start_date = datetime.strptime(message.text, "%Y-%m-%d")
		await state.update_data(start_date=start_date)
		await message.answer(
			"Введите конечную дату в формате ГГГГ-ММ-ДД:",
			reply_markup=AdminKeyboards.back_to_main()
		)
		await state.set_state(StatsStates.WAITING_END_DATE)
	except ValueError:
		await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")


@router.message(StatsStates.WAITING_END_DATE)
async def process_end_date(message: types.Message, state: FSMContext, services: Services):
	"""Обработка конечной даты и вывод статистики"""
	try:
		end_date = datetime.strptime(message.text, "%Y-%m-%d")
		data = await state.get_data()
		start_date = data['start_date']

		stats = await services.admin.get_period_stats(start_date, end_date)

		text = (
			f"📊 <b>Статистика за период</b>\n"
			f"📅 {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}\n\n"
			f"👤 Новых пользователей: <code>{stats['new_users']}</code>\n"
			f"🟢 Активных пользователей: <code>{stats['active_users']}</code>\n"
			f"🔴 Заблокированных: <code>{stats['banned_users']}</code>\n"
			f"📢 Изменений каналов: <code>{stats['channel_changes']}</code>\n"
			f"✉️ Уведомлений отправлено: <code>{stats['notifications_sent']}</code>"
		)

		await message.answer(text, parse_mode=ParseMode.HTML)
		await state.clear()
	except ValueError:
		await message.answer("❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД")
