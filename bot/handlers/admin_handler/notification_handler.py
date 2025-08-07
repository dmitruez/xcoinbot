from aiogram import Router, types, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ...keyboards.admin_keyboard import AdminKeyboards
from ...services import Services
from ...states.admin_states import NotificationStates
from ...utils.loggers import handlers as logger


router = Router(name=__name__)


@router.message(Command('edit_notification'))
@router.callback_query(F.data == "admin_notif")
async def notification_menu(callback: types.CallbackQuery | types.Message, state: FSMContext):
	"""Меню управления уведомлениями"""
	state_data = await state.get_data()
	if delete_message := state_data.get("delete_message"):
		try:
			await delete_message.delete()
		except Exception as e:
			pass
		await state.clear()
	
	text = ("📝 <b>Управление рассылкой</b>\n\n"
	        "Здесь вы можете настроить шаблон уведомления и запустить рассылку.")
	
	if isinstance(callback, types.CallbackQuery):
		await callback.message.edit_text(
			text=text,
			reply_markup=AdminKeyboards.notification_menu()
		)
		await callback.answer()
	else:
		await callback.answer(
			text=text,
			reply_markup=AdminKeyboards.notification_menu()
		)


@router.callback_query(F.data == "notif_edit_text")
async def edit_text(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Редактирование текста уведомления"""
	template = await services.notification.get_template()
	await callback.message.edit_text(
		"📝 <b>Редактирование текста рассылки</b>\n\n"
		"Отправьте новый текст уведомления. Вы можете использовать плейсхолдеры:\n"
		"• <code>&title</code> - название канала\n"
		"• <code>&link</code> - ссылка на канал\n\n"
		f"Текущий текст:\n<pre>{template.text}</pre>",
		reply_markup=AdminKeyboards.back_to_notification()
	)
	await state.set_state(NotificationStates.EDIT_TEXT)
	await callback.answer()


@router.message(NotificationStates.EDIT_TEXT)
async def save_notification_text(message: types.Message, state: FSMContext, services: Services):
	"""Сохранение нового текста уведомления"""
	await services.notification.update_text(message.text)
	await state.clear()
	await message.answer("✅ Текст уведомления успешно обновлен!")


@router.callback_query(F.data == "notif_edit_media")
async def edit_notif_media(
		callback: types.CallbackQuery,
		state: FSMContext,
		services: Services
):
	"""Меню управления медиа"""
	notif_data = await services.notification.get_template()
	has_media = notif_data.media_id is not None
	text = (
			"🖼 <b>Управление медиа-контентом</b>\n\n"
			"Текущий статус: " + ("✅ Медиа прикреплено" if has_media else "❌ Медиа отсутствует") + "\n\n"
			                                                                                       "Отправьте новое фото/видео/GIF-изображение или документ, "
			                                                                                       "либо нажмите кнопку удаления."
	)
	await callback.message.edit_text(
		text,
		reply_markup=AdminKeyboards.adaptive_media_keyboard(has_media, 'notif')
	)
	await state.set_state(NotificationStates.UPLOAD_MEDIA)
	await callback.answer()


@router.message(NotificationStates.UPLOAD_MEDIA, F.content_type.in_({
	ContentType.PHOTO,
	ContentType.VIDEO,
	ContentType.ANIMATION,
	ContentType.DOCUMENT
}))
async def save_notif_media(
		message: types.Message,
		state: FSMContext,
		services: Services
):
	"""Сохранение медиа для рассылки"""
	# Определяем тип и file_id медиа
	if message.photo:
		media_type = "photo"
		media_id = message.photo[-1].file_id
	elif message.video:
		media_type = "video"
		media_id = message.video.file_id
	elif message.animation:
		media_type = "animation"
		media_id = message.animation.file_id
	elif message.document:
		media_type = "document"
		media_id = message.document.file_id
	else:
		await message.answer("❌ Неподдерживаемый тип медиа")
		return
	
	# Сохраняем медиа
	await services.notification.update_media(media_type, media_id)
	await message.answer("✅ Медиа успешно обновлено!")
	await state.clear()


@router.callback_query(F.data == "notif_remove_media")
async def remove_welcome_media(
		callback: types.CallbackQuery,
		services: Services
):
	"""Удаление медиа из приветствия"""
	await services.welcome.remove_media()
	await callback.answer("✅ Медиа успешно удалено!", show_alert=True)
	await notification_menu(callback, state=None, services=services)


@router.callback_query(F.data == "notif_manage_buttons")
async def manage_notification_buttons(callback: types.CallbackQuery, services: Services):
	"""Управление кнопками уведомления"""
	template = await services.notification.get_template()
	has_buttons = template.has_buttons()
	
	if not has_buttons:
		text = "ℹ Кнопки в уведомлении не настроены"
	else:
		button_types = {
			"url": "🌐 Ссылка",
			"text": "💬 Текст"
		}
		buttons_list = []
		for i, btn in enumerate(template.buttons):
			btn_type = button_types.get(btn.button_type, "❓ Неизвестный тип")
			buttons_list.append(f"{i + 1}. {btn.text} ({btn_type})")
		
		text = f"🔘 <b>Текущие кнопки:</b>\n\n" + "\n".join(buttons_list)
	
	await callback.message.edit_text(
		f"🔘 <b>Управление кнопками уведомления</b>\n\n{text}",
		
		reply_markup=AdminKeyboards.buttons_menu(has_buttons, 'notif')
	)
	await callback.answer()


@router.callback_query(F.data == "notif_add_button")
async def add_button_start(callback: types.CallbackQuery, state: FSMContext):
	"""Начало добавления кнопки"""
	await callback.message.edit_text(
		"📌 Выберите тип кнопки:",
		reply_markup=AdminKeyboards.button_type_keyboard('notif')
	)
	await state.set_state(NotificationStates.SELECT_BUTTON_TYPE)
	await callback.answer()


@router.callback_query(
	NotificationStates.SELECT_BUTTON_TYPE,
	F.data.in_(["notif_type_url", "notif_type_text"])
)
async def select_button_type(callback: types.CallbackQuery, state: FSMContext):
	"""Обработка выбора типа кнопки"""
	button_type = "url" if callback.data == "notif_type_url" else "text"
	await state.update_data(button_type=button_type)
	
	back_kb = InlineKeyboardBuilder()
	back_kb.button(text="◀️ Назад", callback_data="notif_add_button")
	
	await callback.message.edit_text(
		"✏️ Введите название кнопки:",
		reply_markup=back_kb.as_markup()
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
	data = await state.get_data()
	
	if data.get('button_type') == "url":
		await message.answer("🌐 Введите URL для кнопки:")
		await state.set_state(NotificationStates.WAITING_BUTTON_URL)
	else:
		await message.answer("📝 Введите текст, который будет отправляться при нажатии на кнопку:")
		await state.set_state(NotificationStates.WAITING_BUTTON_CONTENT)


@router.message(NotificationStates.WAITING_BUTTON_URL)
async def add_button_url(message: types.Message, state: FSMContext, services: Services):
	"""Обработка URL кнопки"""
	data = await state.get_data()
	button_text = data.get('button_text')
	
	# Простая валидация URL
	if not message.text.startswith(('http://', 'https://')):
		return await message.answer("❌ URL должен начинаться с http:// или https://")
	
	if await services.notification.add_button(
			button_text=button_text,
			button_type='url',
			button_value=message.text
	):
		await message.answer("✅ URL-Кнопка успешно добавлена!")
	else:
		await message.answer("❌ Не удалось добавить кнопку (превышен лимит?)")
	
	await state.clear()


@router.message(NotificationStates.WAITING_BUTTON_CONTENT)
async def add_button_content(message: types.Message, state: FSMContext, services: Services):
	"""Обработка контента для текстовой кнопки"""
	# Получаем сохраненный текст кнопки
	data = await state.get_data()
	button_text = data.get('button_text')
	
	# Сохраняем текст как контент
	if await services.notification.add_button(
			button_text=button_text,
			button_type="text",
			button_value=message.text
	):
		await message.answer("✅ Текстовая кнопка успешно добавлена!")
	else:
		await message.answer("❌ Не удалось добавить кнопку (превышен лимит?)")
	
	await state.clear()

@router.callback_query(F.data == "notif_remove_button")
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
	
	if await services.notification.remove_button(button_index):
		await callback.answer("✅ Кнопка успешно удалена!", show_alert=True)
	else:
		await callback.answer("❌ Не удалось удалить кнопку", show_alert=True)
	
	# Обновляем меню кнопок
	await manage_notification_buttons(callback, services)


@router.callback_query(F.data == "notif_clear_buttons")
async def clear_buttons(callback: types.CallbackQuery, services: Services):
	"""Очистка всех кнопок"""
	await services.notification.clear_buttons()
	await callback.answer("✅ Все кнопки удалены!", show_alert=True)
	await manage_notification_buttons(callback, services)


@router.callback_query(F.data == "notif_preview")
async def preview_notification(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Предпросмотр уведомления"""
	
	backup_channel = await services.channel.get_backup_channel()
	if not backup_channel:
		await callback.message.answer(
			f"❌<b>РЕЗЕРВНЫЙ КАНАЛ НЕ НАСТРОЕН</b> ❌\n\n"
			f"Пожалуйста добавьте его в ближайшее время"
		)
		return
	text, media_type, media_id, buttons = await services.notification.format_message(backup_channel)
	keyboard = await services.notification.format_keyboard(buttons)
	
	await callback.message.delete()
	try:
		await callback.message.answer(
			"👀 <b>Предпросмотр уведомления:</b>",
			reply_markup=AdminKeyboards.back_to_notification()
		)
		user_id = callback.message.chat.id
		msg = await services.notification.send_message(user_id, text, media_type, media_id, keyboard)
		if msg:
			await state.update_data(delete_message=msg)
		await callback.answer()
	except Exception as e:
		await callback.answer(f"❌ Ошибка при показе: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("notif_textbtn:"))
async def handle_welcome_button(
		callback: types.CallbackQuery,
		services: Services
):
	"""Обработка нажатий на кнопки рассылочного сообщения"""
	try:
		button_id = callback.data.split(":", 1)[1]
		
		button = await services.notification.get_button_by_id(button_id)
		
		if not button:
			await callback.answer("❌ Кнопка не найдена", show_alert=True)
			return
		
		# Отправляем текстовый контент
		await callback.message.answer(button.value)
		await callback.answer()
		
	
	except Exception as e:
		logger.error(f"Ошибка обработки кнопки: {e}")
		await callback.answer("❌ Произошла ошибка", show_alert=True)
