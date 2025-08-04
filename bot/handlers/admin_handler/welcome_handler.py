from aiogram import Router, types, F
from aiogram.types import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ...keyboards.admin_keyboard import AdminKeyboards
from ...services import Services
from ...states.admin_states import WelcomeStates
from ...utils.loggers import handlers as logger


router = Router(name=__name__)


# Меню управления приветственным сообщением
@router.message(Command('edit_welcome'))
@router.callback_query(F.data == "admin_welcome")
async def welcome_menu(
		callback: types.CallbackQuery | types.Message,
		state: FSMContext | None,
		services: Services
):
	"""Меню управления приветственным сообщением"""
	# Очистка предыдущего состояния и сообщений
	state_data = await state.get_data()
	if delete_message := state_data.get("delete_message"):
		try:
			await delete_message.delete()
		except:
			pass
		await state.clear()
	
	text = (
		"👋 <b>Управление приветственным сообщением</b>\n\n"
		"Здесь вы можете настроить сообщение, которое видят новые пользователи."
	)
	
	
	# Отправка/редактирование сообщения
	if isinstance(callback, types.CallbackQuery):
		await callback.message.edit_text(
			text,
			reply_markup=AdminKeyboards.admin_welcome()
		)
		await callback.answer()
	else:
		await callback.answer(
			text,
			reply_markup=AdminKeyboards.admin_welcome()
		)


# Редактирование текста приветствия
@router.callback_query(F.data == "welcome_edit_text")
async def edit_welcome_text(
		callback: types.CallbackQuery,
		state: FSMContext,
		services: Services
):
	"""Редактирование текста приветствия"""
	welcome_data = await services.welcome.get_welcome_data()
	
	# Создаем клавиатуру для возврата
	back_kb = InlineKeyboardBuilder()
	back_kb.button(text="◀️ Назад", callback_data="admin_welcome")
	
	await callback.message.edit_text(
		"📝 <b>Редактирование текста приветствия</b>\n\n"
		"Отправьте новый текст сообщения. Поддерживается HTML-разметка.\n"
		"Воздержитесь от простых <> потому что бот воспринимает это как тег html\n"
		"Используйте:\n"
		"<code>&link</code> - Актуальная ссылка на канал\n"
		"<code>&title</code> - Название канала\n\n"
		f"Текущий текст:\n<pre>{welcome_data.get('text', '')}</pre>",
		reply_markup=back_kb.as_markup()
	)
	await state.set_state(WelcomeStates.EDIT_TEXT)
	await callback.answer()


@router.message(WelcomeStates.EDIT_TEXT)
async def save_welcome_text(
		message: types.Message,
		state: FSMContext,
		services: Services
):
	"""Сохранение текста приветствия"""
	await services.welcome.update_text(message.text)
	await state.clear()
	await message.answer("✅ Текст приветствия успешно обновлен!")


# Управление медиа-контентом
@router.callback_query(F.data == "welcome_edit_media")
async def edit_welcome_media(
		callback: types.CallbackQuery,
		state: FSMContext,
		services: Services
):
	"""Меню управления медиа"""
	welcome_data = await services.welcome.get_welcome_data()
	has_media = welcome_data.get('media_file_id') is not None
	
	text = (
			"🖼 <b>Управление медиа-контентом</b>\n\n"
			"Текущий статус: " + ("✅ Медиа прикреплено" if has_media else "❌ Медиа отсутствует") + "\n\n"
			                                                                                       "Отправьте новое фото/видео/GIF-изображение или документ, "
			                                                                                       "либо нажмите кнопку удаления."
	)
	
	# Создаем адаптивную клавиатуру
	kb_builder = InlineKeyboardBuilder()
	if has_media:
		kb_builder.button(text="❌ Удалить медиа", callback_data="welcome_remove_media")
	kb_builder.button(text="◀️ Назад", callback_data="admin_welcome")
	kb_builder.adjust(1)  # Каждая кнопка на новой строке
	
	await callback.message.edit_text(
		text,
		reply_markup=kb_builder.as_markup()
	)
	await state.set_state(WelcomeStates.UPLOAD_MEDIA)
	await callback.answer()


@router.message(WelcomeStates.UPLOAD_MEDIA, F.content_type.in_({
	ContentType.PHOTO,
	ContentType.VIDEO,
	ContentType.ANIMATION,
	ContentType.DOCUMENT
}))
async def save_welcome_media(
		message: types.Message,
		state: FSMContext,
		services: Services
):
	"""Сохранение медиа для приветствия"""
	# Определяем тип и file_id медиа
	if message.photo:
		media_type = "photo"
		media_file_id = message.photo[-1].file_id
	elif message.video:
		media_type = "video"
		media_file_id = message.video.file_id
	elif message.animation:
		media_type = "animation"
		media_file_id = message.animation.file_id
	elif message.document:
		media_type = "document"
		media_file_id = message.document.file_id
	else:
		await message.answer("❌ Неподдерживаемый тип медиа")
		return
	
	# Сохраняем медиа
	await services.welcome.update_media(media_type, media_file_id)
	await message.answer("✅ Медиа успешно обновлено!")
	await state.clear()


@router.callback_query(F.data == "welcome_remove_media")
async def remove_welcome_media(
		callback: types.CallbackQuery,
		services: Services
):
	"""Удаление медиа из приветствия"""
	await services.welcome.remove_media()
	await callback.answer("✅ Медиа успешно удалено!", show_alert=True)
	await welcome_menu(callback, state=None, services=services)


# Управление кнопками приветствия
@router.callback_query(F.data == "welcome_manage_buttons")
async def manage_welcome_buttons(
		callback: types.CallbackQuery,
		services: Services
):
	"""Управление кнопками приветствия"""
	welcome_data = await services.welcome.get_welcome_data()
	buttons = welcome_data.get('buttons', [])
	
	# Формируем текст с текущими кнопками
	button_types = {
		"url": "🌐 Ссылка",
		"text": "💬 Текст"
	}
	
	if not buttons:
		text = "ℹ Кнопки в сообщении не настроены"
	else:
		buttons_list = []
		for i, btn in enumerate(buttons):
			btn_type = button_types.get(btn.get('type', 'url'), "❓ Неизвестный тип")
			buttons_list.append(f"{i + 1}. {btn['text']} ({btn_type})")
		
		text = f"🔘 <b>Текущие кнопки:</b>\n\n" + "\n".join(buttons_list)
	
	# Создаем адаптивную клавиатуру
	kb_builder = InlineKeyboardBuilder()
	kb_builder.button(text="➕ Добавить кнопку", callback_data="welcome_add_button")
	
	if buttons:
		kb_builder.button(text="➖ Удалить кнопку", callback_data="welcome_remove_button")
		kb_builder.button(text="🧹 Очистить все", callback_data="welcome_clear_buttons")
	
	kb_builder.button(text="◀️ Назад", callback_data="admin_welcome")
	kb_builder.adjust(1, 2 if buttons else 1, 1)  # Адаптивная раскладка
	
	await callback.message.edit_text(
		f"🔘 <b>Управление кнопками приветствия</b>\n\n{text}",
		reply_markup=kb_builder.as_markup()
	)
	await callback.answer()


@router.callback_query(F.data == "welcome_add_button")
async def add_button_start(
		callback: types.CallbackQuery,
		state: FSMContext
):
	"""Начало добавления кнопки: выбор типа"""
	builder = InlineKeyboardBuilder()
	builder.button(text="🔗 URL-кнопка", callback_data="button_type_url")
	builder.button(text="💬 Текстовая кнопка", callback_data="button_type_text")
	builder.button(text="◀️ Назад", callback_data="welcome_manage_buttons")
	builder.adjust(1)
	
	await callback.message.edit_text(
		"📌 Выберите тип кнопки:",
		reply_markup=builder.as_markup()
	)
	await state.set_state(WelcomeStates.SELECT_BUTTON_TYPE)
	await callback.answer()


@router.callback_query(
	WelcomeStates.SELECT_BUTTON_TYPE,
	F.data.in_(["button_type_url", "button_type_text"])
)
async def select_button_type(
		callback: types.CallbackQuery,
		state: FSMContext
):
	"""Обработка выбора типа кнопки"""
	button_type = "url" if callback.data == "button_type_url" else "text"
	await state.update_data(button_type=button_type)
	
	back_kb = InlineKeyboardBuilder()
	back_kb.button(text="◀️ Назад", callback_data="welcome_add_button")
	
	await callback.message.edit_text(
		"✏️ Введите текст для кнопки:",
		reply_markup=back_kb.as_markup()
	)
	await state.set_state(WelcomeStates.WAITING_BUTTON_TEXT)
	await callback.answer()


@router.message(WelcomeStates.WAITING_BUTTON_TEXT)
async def add_button_text(
		message: types.Message,
		state: FSMContext
):
	"""Обработка текста кнопки"""
	# Валидация длины текста
	if len(message.text) > 20:
		return await message.answer("❌ Текст кнопки не должен превышать 20 символов")
	if len(message.text) < 2:
		return await message.answer("❌ Текст кнопки должен быть не менее 2 символов")
	
	await state.update_data(button_text=message.text)
	data = await state.get_data()
	
	if data.get('button_type') == "url":
		await message.answer("🌐 Введите URL для кнопки:")
		await state.set_state(WelcomeStates.WAITING_BUTTON_URL)
	else:
		await message.answer("📝 Введите текст, который будет отправляться при нажатии на кнопку:")
		await state.set_state(WelcomeStates.WAITING_BUTTON_CONTENT)


@router.message(WelcomeStates.WAITING_BUTTON_URL)
async def add_button_url(
		message: types.Message,
		state: FSMContext,
		services: Services
):
	"""Обработка URL кнопки"""
	# Получаем сохраненный текст кнопки
	data = await state.get_data()
	button_text = data.get('button_text')
	
	# Валидация URL
	if not message.text.startswith(('http://', 'https://')):
		return await message.answer("❌ URL должен начинаться с http:// или https://")
	
	# Добавляем кнопку
	if await services.welcome.add_button(
			button_text=button_text,
			button_type="url",
			button_value=message.text
	):
		await message.answer("✅ URL-кнопка успешно добавлена!")
	else:
		await message.answer("❌ Не удалось добавить кнопку (превышен лимит?)")
	
	await state.clear()


@router.message(WelcomeStates.WAITING_BUTTON_CONTENT)
async def add_button_content(
		message: types.Message,
		state: FSMContext,
		services: Services
):
	"""Обработка контента для текстовой кнопки"""
	# Получаем сохраненный текст кнопки
	data = await state.get_data()
	button_text = data.get('button_text')
	
	# Сохраняем текст как контент
	if await services.welcome.add_button(
			button_text=button_text,
			button_type="text",
			button_value=message.text
	):
		await message.answer("✅ Текстовая кнопка успешно добавлена!")
	else:
		await message.answer("❌ Не удалось добавить кнопку (превышен лимит?)")
	
	await state.clear()


@router.callback_query(F.data == "welcome_remove_button")
async def remove_button_start(
		callback: types.CallbackQuery,
		services: Services
):
	"""Начало удаления кнопки"""
	welcome_data = await services.welcome.get_welcome_data()
	buttons = welcome_data.get('buttons', [])
	
	if not buttons:
		return await callback.answer("ℹ Нет кнопок для удаления", show_alert=True)
	
	# Создаем клавиатуру с кнопками для удаления
	kb_builder = InlineKeyboardBuilder()
	for i, btn in enumerate(buttons):
		kb_builder.button(text=f"{i + 1}. {btn['text']}", callback_data=f"welcome_removebtn_{i}")
	kb_builder.button(text="◀️ Отмена", callback_data="welcome_manage_buttons")
	kb_builder.adjust(1)  # Каждая кнопка на новой строке
	
	await callback.message.edit_text(
		"❌ Выберите кнопку для удаления:",
		reply_markup=kb_builder.as_markup()
	)
	await callback.answer()


@router.callback_query(F.data.startswith("welcome_removebtn_"))
async def remove_button_confirm(
		callback: types.CallbackQuery,
		services: Services
):
	"""Удаление выбранной кнопки"""
	button_index = int(callback.data.split("_")[2])
	
	if await services.welcome.remove_button(button_index):
		await callback.answer("✅ Кнопка успешно удалена!", show_alert=True)
	else:
		await callback.answer("❌ Не удалось удалить кнопку", show_alert=True)
	
	# Возвращаемся в меню управления кнопками
	await manage_welcome_buttons(callback, services)


@router.callback_query(F.data == "welcome_clear_buttons")
async def clear_buttons(
		callback: types.CallbackQuery,
		services: Services
):
	"""Очистка всех кнопок"""
	await services.welcome.clear_buttons()
	await callback.answer("✅ Все кнопки удалены!", show_alert=True)
	await manage_welcome_buttons(callback, services)


# Предпросмотр приветственного сообщения
@router.callback_query(F.data == "welcome_preview")
async def preview_welcome(
		callback: types.CallbackQuery,
		state: FSMContext,
		services: Services
):
	"""Предпросмотр приветственного сообщения"""
	# Получаем текущие данные приветствия
	welcome_data = await services.welcome.get_welcome_data()
	text = welcome_data.get('text', '')
	buttons = welcome_data.get('buttons', [])
	media_type = welcome_data.get('media_type')
	media_file_id = welcome_data.get('media_file_id')
	
	# Формируем клавиатуру из кнопок
	kb_builder = InlineKeyboardBuilder()
	for btn in buttons:
		if btn.get('type') == "text":
			# Для текстовых кнопок используем callback_data с префиксом
			kb_builder.button(
				text=btn['text'],
				callback_data=f"welcome_textbtn:{btn['value']}"
			)
		else:
			# Для URL-кнопок используем стандартный URL
			kb_builder.button(
				text=btn['text'],
				url=btn['value']
			)
	kb_builder.adjust(1)  # Одна кнопка в ряд
	
	try:
		# Отправляем заголовок предпросмотра
		await callback.message.answer(
			"👀 <b>Предпросмотр приветственного сообщения:</b>",
			reply_markup=InlineKeyboardBuilder()
			.button(text="◀️ Назад", callback_data="admin_welcome")
			.as_markup()
		)
		
		# Отправляем само сообщение
		if media_type and media_file_id:
			# Для каждого типа медиа свой метод отправки
			if media_type == "photo":
				msg = await callback.bot.send_photo(
					chat_id=callback.message.chat.id,
					photo=media_file_id,
					caption=text,
					reply_markup=kb_builder.as_markup()
				)
			elif media_type == "video":
				msg = await callback.bot.send_video(
					chat_id=callback.message.chat.id,
					video=media_file_id,
					caption=text,
					reply_markup=kb_builder.as_markup()
				)
			elif media_type == "animation":
				msg = await callback.bot.send_animation(
					chat_id=callback.message.chat.id,
					animation=media_file_id,
					caption=text,
					reply_markup=kb_builder.as_markup()
				)
			elif media_type == "document":
				msg = await callback.bot.send_document(
					chat_id=callback.message.chat.id,
					document=media_file_id,
					caption=text,
					reply_markup=kb_builder.as_markup()
				)
			else:
				# Если тип медиа не поддерживается, отправляем текст
				msg = await callback.bot.send_message(
					chat_id=callback.message.chat.id,
					text=text,
					reply_markup=kb_builder.as_markup()
				)
		else:
			# Отправка только текста
			msg = await callback.bot.send_message(
				chat_id=callback.message.chat.id,
				text=text,
				reply_markup=kb_builder.as_markup()
			)
		
		# Сохраняем сообщение для последующего удаления
		await state.update_data(delete_message=msg)
		await callback.answer()
	
	except Exception as e:
		await callback.answer(f"❌ Ошибка при показе: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith("welcome_textbtn:"))
async def handle_welcome_button(
		callback: types.CallbackQuery,
		services: Services
):
	"""Обработка нажатий на кнопки приветственного сообщения"""
	try:
		# Извлекаем ID кнопки из callback_data
		button_id = callback.data.split(":", 1)[1]
		
		# Ищем кнопку в хранилище
		button = await services.welcome.get_button_by_id(button_id)
		
		if not button:
			await callback.answer("❌ Кнопка не найдена", show_alert=True)
			return
		
		if button.get('type') == "text":
			# Отправляем текстовый контент
			await callback.message.answer(button['value'])
			await callback.answer()
		
		elif button.get('type') == "url":
			# Для URL-кнопок просто отвечаем (можно ничего не делать)
			await callback.answer()
	
	except Exception as e:
		logger.error(f"Ошибка обработки кнопки: {e}")
		await callback.answer("❌ Произошла ошибка", show_alert=True)