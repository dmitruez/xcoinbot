from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.methods import delete_message

from xcoinbot.bot.keyboards.admin_keyboard import AdminKeyboards
from xcoinbot.bot.services import Services
from xcoinbot.bot.states.admin_states import NotificationStates


router = Router(name=__name__)


@router.message(Command('edit_notification'))
async def redirect_notification_menu(message: types.Message, state: FSMContext):
	await notification_menu(message, state)


@router.callback_query(F.data == "admin_notification")
async def notification_menu(callback: types.CallbackQuery | types.Message, state: FSMContext):
	"""Меню управления уведомлениями"""
	state_data = await state.get_data()
	if delete_message := state_data.get("delete_message"):
		await delete_message.delete()
		await state.clear()

	if isinstance(callback, types.CallbackQuery):

		await callback.message.edit_text(
			"📝 <b>Управление рассылкой</b>\n\n"
			"Здесь вы можете настроить шаблон уведомления и запустить рассылку.",
			reply_markup=AdminKeyboards.notification_menu()
		)
		await callback.answer()
	else:
		await callback.answer(
			"📝 <b>Управление рассылкой</b>\n\n"
			"Здесь вы можете настроить шаблон уведомления и запустить рассылку.",
			reply_markup=AdminKeyboards.notification_menu()
		)


@router.callback_query(F.data == "admin_edit_text")
async def edit_text(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Редактирование текста уведомления"""
	template = await services.notification.get_template()
	await callback.message.edit_text(
		"📝 <b>Редактирование текста рассылки</b>\n\n"
		"Отправьте новый текст уведомления. Вы можете использовать плейсхолдеры:\n"
		"• <code>&title</code> - название канала\n"
		"• <code>&link</code> - ссылка на канал\n\n"
		"Текущий текст:\n<pre>{}</pre>".format(template.text),
		reply_markup=AdminKeyboards.back_to_notification()
	)
	await state.set_state(NotificationStates.EDIT_TEXT)
	await callback.answer()


@router.message(NotificationStates.EDIT_TEXT)
async def save_notification_text(message: types.Message, state: FSMContext, services: Services):
	"""Сохранение нового текста уведомления"""
	await services.notification.update_template_text(message.text)
	await state.clear()
	await message.answer("✅ Текст уведомления успешно обновлен!")


@router.callback_query(F.data == "admin_manage_buttons")
async def manage_notification_buttons(callback: types.CallbackQuery, services: Services):
	"""Управление кнопками уведомления"""
	template = await services.notification.get_template()

	if not template.buttons:
		text = "ℹ Кнопки в уведомлении не настроены"
	else:
		buttons_list = "\n".join(
			f"{i + 1}. {btn[0]} - {btn[1]}"
			for i, btn in enumerate(template.buttons)
		)
		text = f"🔘 <b>Текущие кнопки:</b>\n\n{buttons_list}"

	await callback.message.edit_text(
		f"🔘 <b>Управление кнопками уведомления</b>\n\n{text}",

		reply_markup=AdminKeyboards.buttons_menu()
	)
	await callback.answer()


@router.callback_query(F.data == "admin_add_button")
async def add_button_start(callback: types.CallbackQuery, state: FSMContext):
	"""Начало добавления кнопки"""
	await callback.message.edit_text(
		"✏️ Введите текст для новой кнопки:",
		reply_markup=AdminKeyboards.back_to_buttons()
	)
	await state.set_state(NotificationStates.WAITING_BUTTON_TEXT)
	await callback.answer()


@router.message(NotificationStates.WAITING_BUTTON_TEXT)
async def add_button_text(message: types.Message, state: FSMContext):
	"""Обработка текста кнопки"""
	if len(message.text) > 20:
		return await message.answer("❌ Текст кнопки не должен превышать 20 символов")

	if len(message.text) < 2:
		return await message.answer("❌ Текст кнопки должен быть не менее 2 символов")

	await state.update_data(button_text=message.text)
	await message.answer("🌐 Введите URL для кнопки:")
	await state.set_state(NotificationStates.WAITING_BUTTON_URL)


@router.message(NotificationStates.WAITING_BUTTON_URL)
async def add_button_url(message: types.Message, state: FSMContext, services: Services):
	"""Обработка URL кнопки"""
	data = await state.get_data()
	button_text = data.get('button_text')

	# Простая валидация URL
	if not message.text.startswith(('http://', 'https://')):
		return await message.answer("❌ URL должен начинаться с http:// или https://")

	if await services.notification.add_template_button(button_text, message.text):
		await message.answer("✅ Кнопка успешно добавлена!")
	else:
		await message.answer("❌ Не удалось добавить кнопку (превышен лимит?)")

	await state.clear()


@router.callback_query(F.data == "admin_remove_button")
async def remove_button_start(callback: types.CallbackQuery, services: Services):
	"""Начало удаления кнопки"""
	template = await services.notification.get_template()

	if not template.buttons:
		return await callback.answer("ℹ Нет кнопок для удаления", show_alert=True)

	await callback.message.edit_text(
		"❌ Выберите кнопку для удаления:",
		reply_markup=AdminKeyboards.remove_buttons(template)
	)
	await callback.answer()


@router.callback_query(F.data.startswith("remove_button_"))
async def remove_button_confirm(callback: types.CallbackQuery, services: Services):
	"""Подтверждение удаления кнопки"""
	button_index = int(callback.data.split("_")[2])

	if await services.notification.remove_template_button(button_index):
		await callback.answer("✅ Кнопка успешно удалена!", show_alert=True)
	else:
		await callback.answer("❌ Не удалось удалить кнопку", show_alert=True)

	# Обновляем меню кнопок
	await manage_notification_buttons(callback, services)


@router.callback_query(F.data == "admin_clear_buttons")
async def clear_buttons(callback: types.CallbackQuery, services: Services):
	"""Очистка всех кнопок"""
	await services.notification.clear_template_buttons()
	await callback.answer("✅ Все кнопки удалены!", show_alert=True)
	await manage_notification_buttons(callback, services)


@router.callback_query(F.data == "admin_preview_notification")
async def preview_notification(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Предпросмотр уведомления"""

	backup_channel = await services.channel.get_backup_channel()
	if not backup_channel:
		await callback.message.answer(
			f"❌<b>РЕЗЕРВНЫЙ КАНАЛ НЕ НАСТРОЕН</b> ❌\n\n"
			f"Пожалуйста добавьте его в ближайшее время"
		)
		return
	text, keyboard = await services.notification.format_notification(backup_channel)

	await callback.message.delete()
	await callback.message.answer(
		"👀 <b>Предпросмотр уведомления:</b>",
		reply_markup=AdminKeyboards.back_to_notification()
	)
	delete_message = await callback.message.answer(
		text,
		reply_markup=keyboard,
		disable_web_page_preview=True
	)
	await state.update_data(delete_message=delete_message)
	await callback.answer()

@router.callback_query(F.data == "admin_send_notification")
async def send_notification_confirmation(callback: types.CallbackQuery, services: Services):
	"""Подтверждение отправки рассылки"""
	await callback.answer("❌ Пока в разработке ❌")
# 	user_count = await services.user.get_users_for_notification()
# 	await callback.message.edit_text(
# 		f"✉️ <b>Подтвердите отправку рассылки</b>\n\n"
# 		f"Уведомление будет отправлено <b>всем пользователям</b> (всего: {user_count}).\n"
# 		"Вы уверены, что хотите начать рассылку?",
#
# 		reply_markup=AdminKeyboards.confirm_send_menu()
# 	)
# 	await callback.answer()
#
#
# @router.callback_query(F.data == "confirm_send")
# async def start_notification(callback: types.CallbackQuery, services: Services):
# 	"""Запуск рассылки уведомлений"""
# 	# Показываем сообщение о начале рассылки
# 	await callback.message.edit_text(
# 		"⏳ <b>Начата рассылка уведомлений...</b>\n"
# 		"Это может занять некоторое время. Статус будет обновлен по завершении.",
# 		parse_mode=ParseMode.HTML
# 	)
#
# 	# Запускаем рассылку
# 	success_count = await services.notification.notify_channel_change()
#
# 	# Обновляем сообщение с результатами
# 	total_users = await services.user.get_total_users()
# 	await callback.message.edit_text(
# 		f"✅ <b>Рассылка завершена!</b>\n\n"
# 		f"• Успешно отправлено: <b>{success_count}</b>\n"
# 		f"• Не удалось отправить: <b>{total_users - success_count}</b>\n"
# 		f"• Всего получателей: <b>{total_users}</b>",
#
# 		reply_markup=AdminKeyboards.back_to_notification()
# 	)
# 	await callback.answer()
