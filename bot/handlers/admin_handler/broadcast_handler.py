import uuid
from typing import List, Optional

from aiogram import Router, types, F
from aiogram.enums import ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from ...keyboards.admin_keyboard import BroadCastKeyboards, AdminKeyboards
from ...services import Services
from ...states.admin_states import BroadcastStates
from ...models import BroadcastMessage, Button
from ...utils.loggers import handlers as logger


router = Router(name=__name__)


# Меню управления рассылками
@router.message(Command('broadcast'))
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_menu(callback: types.CallbackQuery | types.Message, state: FSMContext):
	"""Меню управления рассылками"""
	state_data = await state.get_data()
	if delete_message := state_data.get("delete_message"):
		try:
			await delete_message.delete()
		except:
			pass
		await state.clear()
	
	text = ("📢 <b>Управление рассылками</b>\n\n"
	        "Здесь вы можете выполнить быструю рассылку или посмотреть историю.")
	
	if isinstance(callback, types.CallbackQuery):
		await callback.message.edit_text(
			text=text,
			reply_markup=BroadCastKeyboards.broadcast_menu()
		)
		await callback.answer()
	else:
		await callback.answer(
			text=text,
			reply_markup=BroadCastKeyboards.broadcast_menu()
		)


# Быстрая рассылка
@router.callback_query(F.data == "broadcast_quick")
async def quick_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
	"""Начало быстрой рассылки"""
	await state.update_data(buttons=[])
	await callback.message.edit_text(
		"✉️ <b>Быстрая рассылка</b>\n\n"
		"Отправьте сообщение, которое будет разослано всем пользователям. "
		"Можно использовать текст, фото, видео или документы.",
		reply_markup=BroadCastKeyboards.back_to_broadcast()
	)
	await state.set_state(BroadcastStates.WAITING_CONTENT)
	await callback.answer()


@router.message(BroadcastStates.WAITING_CONTENT)
async def process_broadcast_content(message: types.Message, state: FSMContext, services: Services):
	"""Обработка контента для рассылки"""
	# Сохраняем данные сообщения
	content = {
		"text": message.html_text if message.text else message.caption,
		"media_type": message.content_type,
		"media_id": None
	}
	
	if message.photo:
		content["media_id"] = message.photo[-1].file_id
	elif message.video:
		content["media_id"] = message.video.file_id
	elif message.document:
		content["media_id"] = message.document.file_id
	
	await state.update_data(content=content)
	
	# Запрашиваем подтверждение
	await message.answer(
		"✅ Контент для рассылки получен. Хотите добавить кнопки?",
		reply_markup=BroadCastKeyboards.confirm_add_buttons()
	)


@router.callback_query(F.data == "broadcast_manage_buttons")
async def broadcast_manage_buttons(callback: types.CallbackQuery, state: FSMContext):
	# Запрашиваем подтверждение
	await callback.message.edit_text(
		"✅ Контент для рассылки получен. Хотите добавить кнопки?",
		reply_markup=BroadCastKeyboards.confirm_add_buttons()
	)


@router.callback_query(F.data == "broadcast_add_button")
async def broadcast_add_buttons(callback: types.CallbackQuery, state: FSMContext):
	"""Добавление кнопок к рассылке"""
	await callback.message.edit_text(
		"📌 Выберите тип кнопки:",
		reply_markup=AdminKeyboards.button_type_keyboard('broadcast')
	)
	await state.set_state(BroadcastStates.SELECT_BUTTON_TYPE)
	await callback.answer()


@router.callback_query(
	BroadcastStates.SELECT_BUTTON_TYPE,
	F.data.in_(["broadcast_type_url", "broadcast_type_text"])
)
async def select_button_type(
		callback: types.CallbackQuery,
		state: FSMContext
):
	"""Обработка выбора типа кнопки"""
	button_type = "url" if callback.data == "broadcast_type_url" else "text"
	await state.update_data(button_type=button_type)
	
	back_kb = InlineKeyboardBuilder()
	back_kb.button(text="◀️ Назад", callback_data="broadcast_add_button")
	
	await callback.message.edit_text(
		"✏️ Введите название кнопки:",
		reply_markup=back_kb.as_markup()
	)
	await state.set_state(BroadcastStates.WAITING_BUTTON_TEXT)
	await callback.answer()


@router.message(BroadcastStates.WAITING_BUTTON_TEXT)
async def add_button_text(
		message: types.Message,
		state: FSMContext
):
	"""Обработка текста кнопки"""
	if len(message.text) > 20:
		return await message.answer("❌ Текст кнопки не должен превышать 20 символов")
	
	if len(message.text) < 2:
		return await message.answer("❌ Текст кнопки должен быть не менее 2 символов")
	
	await state.update_data(button_text=message.text)
	data = await state.get_data()
	
	if data.get('button_type') == "url":
		await message.answer("🌐 Введите URL для кнопки:")
		await state.set_state(BroadcastStates.WAITING_BUTTON_URL)
	else:
		await message.answer("📝 Введите текст, который будет отправляться при нажатии на кнопку:")
		await state.set_state(BroadcastStates.WAITING_BUTTON_CONTENT)


@router.message(BroadcastStates.WAITING_BUTTON_URL)
async def add_button_url(
		message: types.Message,
		state: FSMContext
):
	"""Обработка URL кнопки"""
	data = await state.get_data()
	button_text = data.get('button_text')
	
	# Простая валидация URL
	if not message.text.startswith(('http://', 'https://')):
		return await message.answer("❌ URL должен начинаться с http:// или https://")
	
	button_id = str(uuid.uuid4())
	
	button = Button(
		id=button_id,
		text=button_text,
		button_type='url',
		value=message.text
	)
	
	buttons = data.get('buttons', [])
	buttons.append(button)
	await state.update_data(buttons=buttons)
	
	await message.answer(
		"✅ URL-кнопка добавлена. Хотите добавить еще кнопку?",
		reply_markup=BroadCastKeyboards.confirm_add_another()
	)
	await state.set_state(BroadcastStates.CONFIRM_ADD_ANOTHER)


# Обработка контента текстовой кнопки
@router.message(BroadcastStates.WAITING_BUTTON_CONTENT)
async def add_button_content(
		message: types.Message,
		state: FSMContext
):
	"""Обработка контента для текстовой кнопки"""
	data = await state.get_data()
	button_text = data.get('button_text')
	

	button_id = str(uuid.uuid4())
	
	button = Button(
		id=button_id,
		text=button_text,
		button_type='text',
		value=message.text
	)
	
	# Добавляем кнопку к списку
	buttons = data.get('buttons', [])
	buttons.append(button)
	await state.update_data(buttons=buttons)
	
	await message.answer(
		"✅ Текстовая кнопка добавлена. Хотите добавить еще кнопку?",
		reply_markup=BroadCastKeyboards.confirm_add_another()
	)
	await state.set_state(BroadcastStates.CONFIRM_ADD_ANOTHER)


# Подтверждение добавления еще кнопки
@router.callback_query(
	BroadcastStates.CONFIRM_ADD_ANOTHER,
	F.data.in_(["broadcast_add_another", "broadcast_finish_buttons"])
)
async def process_add_another(
		callback: types.CallbackQuery,
		state: FSMContext
):
	"""Обработка подтверждения добавления кнопки"""
	if callback.data == "broadcast_add_another":
		await callback.message.edit_text(
			"📌 Выберите тип кнопки:",
			reply_markup=AdminKeyboards.button_type_keyboard('broadcast')
		)
		await state.set_state(BroadcastStates.SELECT_BUTTON_TYPE)
	else:
		await confirm_broadcast(callback.message, state)
	
	await callback.answer()


# Подтверждение рассылки
async def confirm_broadcast(
		message: types.Message,
		state: FSMContext
):
	"""Подтверждение рассылки с предпросмотром"""
	data = await state.get_data()
	content = data.get('content', {})
	buttons: Optional[List[Button]] = data.get('buttons', None)
	
	keyboard = None
	# Формируем клавиатуру
	if buttons:
		builder = InlineKeyboardBuilder()
		for btn in buttons:
			if btn.button_type == 'url':
				builder.button(text=btn.text, url=btn.value)
			else:
				builder.button(text=btn.text, callback_data=f"preview_btn:{btn.id}")
		builder.adjust(1)  # 1 кнопка в ряд
		keyboard = builder.as_markup()
	
	# Отправляем предпросмотр
	if content['media_type'] == 'photo':
		await message.answer_photo(
			content['media_id'],
			caption=content['text'],
			reply_markup=keyboard
		)
	elif content['media_type'] == 'video':
		await message.answer_video(
			content['media_id'],
			caption=content['text'],
			reply_markup=keyboard
		)
	elif content['media_type'] == 'document':
		await message.answer_document(
			content['media_id'],
			caption=content['text'],
			reply_markup=keyboard
		)
	else:
		await message.answer(
			content['text'],
			reply_markup=keyboard
		)
	
	await message.answer(
		"Вы уверены, что хотите отправить это сообщение всем пользователям?",
		reply_markup=BroadCastKeyboards.confirm_broadcast()
	)
	await state.set_state(BroadcastStates.CONFIRM_BROADCAST)


# Запуск рассылки
@router.callback_query(BroadcastStates.CONFIRM_BROADCAST, F.data == "broadcast_confirm")
async def start_broadcast(
		callback: types.CallbackQuery,
		state: FSMContext,
		services: Services
):
	"""Запуск рассылки"""
	data = await state.get_data()
	content = data.get('content', {})
	buttons = data.get('buttons', [])
	
	# Получаем список активных пользователей
	users = await services.user.get_users_for_notification()
	total_users = len(users)
	
	# Сохраняем в историю
	broadcast_id = await services.broadcast.save_broadcast(
		text=content.get('text', ''),
		media_type=content.get('media_type', 'text'),
		media_id=content.get('media_id'),
		buttons=buttons,
		sent_by=callback.from_user.id,
		total_users=total_users
	)
	
	# Отправляем сообщение
	success = 0
	errors = 0
	
	for user in users:
		try:
			keyboard = None
			# Формируем клавиатуру
			if buttons:
				builder = InlineKeyboardBuilder()
				for btn in buttons:
					if btn.button_type == 'url':
						builder.button(text=btn.text, url=btn.value)
					else:
						builder.button(text=btn.text, callback_data=f"broadcast_textbtn:{broadcast_id}:{btn.id}")
				builder.adjust(1)  # 1 кнопка в ряд
				keyboard = builder.as_markup()
			
			if content['media_type'] == 'photo':
				await callback.bot.send_photo(
					chat_id=user.user_id,
					photo=content['media_id'],
					caption=content['text'],
					reply_markup=keyboard
				)
			elif content['media_type'] == 'video':
				await callback.bot.send_video(
					chat_id=user.user_id,
					video=content['media_id'],
					caption=content['text'],
					reply_markup=keyboard
				)
			elif content['media_type'] == 'document':
				await callback.bot.send_document(
					chat_id=user.user_id,
					document=content['media_id'],
					caption=content['text'],
					reply_markup=keyboard
				)
			else:
				await callback.bot.send_message(
					chat_id=user.user_id,
					text=content['text'],
					reply_markup=keyboard
				)
			success += 1
		except Exception as e:
			logger.error(f"Ошибка отправки пользователю {user.user_id}: {e}")
			await services.user.set_notification_status(user.user_id, False)
			await services.user.ban_user(user.user_id)
			errors += 1
	
	# Обновляем статистику
	await services.broadcast.update_broadcast_stats(broadcast_id, success, errors)
	
	# Форматируем результат
	result_text = (
		f"✅ Рассылка завершена!\n\n"
		f"• Успешно: {success}\n"
		f"• Ошибок: {errors}\n"
		f"• Всего получателей: {total_users}"
	)
	
	await callback.message.answer(
		result_text,
		reply_markup=BroadCastKeyboards.back_to_broadcast()
	)
	
	await state.clear()
	await callback.answer()


# Обработчик нажатий на текстовые кнопки
# Новый обработчик для кликов по кнопкам в предпросмотре
@router.callback_query(F.data.startswith("preview_btn:"))
async def handle_preview_button(
		callback: types.CallbackQuery,
		state: FSMContext
):
	"""Обработка нажатий на кнопки в предпросмотре"""
	try:
		# Получаем индекс кнопки из callback_data
		button_id = callback.data.split(":")[1]
		
		# Получаем данные из состояния
		data = await state.get_data()
		buttons = data.get('buttons', [])
		
		
		button: Button = list(filter(lambda b: b.id == button_id, buttons))[0]
		
		if not button:
			await callback.answer("❌ Кнопка не найдена", show_alert=True)
			return
		
		# Отправляем текстовый контент
		await callback.message.answer(button.value)
		await callback.answer()
	except Exception as e:
		logger.error(f"Ошибка обработки кнопки предпросмотра: {e}")
		await callback.answer("❌ Ошибка при обработке кнопки", show_alert=True)


# Обработчик нажатий на текстовые кнопки
@router.callback_query(F.data.startswith("broadcast_textbtn:"))
async def handle_broadcast_text_button(
		callback: types.CallbackQuery,
		services: Services
):
	"""Обработка нажатий на текстовые кнопки в рассылках"""
	try:
		_, broadcast_id, button_id = callback.data.split(":")
		broadcast: BroadcastMessage = await services.broadcast.get_broadcast_by_id(int(broadcast_id))
		
		
		button: Button = list(filter(lambda b: b.id == button_id, broadcast.buttons))[0]

		await callback.message.answer(button.value)
		await callback.answer()
	except Exception as e:
		logger.error(f"Ошибка обработки кнопки: {e}")
		await callback.answer("❌ Произошла ошибка", show_alert=True)


# Просмотр истории рассылок
@router.callback_query(F.data == "broadcast_history")
async def show_broadcast_history(
		callback: types.CallbackQuery,
		services: Services
):
	"""Показ истории рассылок"""
	broadcasts = await services.broadcast.get_broadcast_history()
	
	if not broadcasts:
		await callback.message.edit_text(
			"📜 История рассылок пуста",
			reply_markup=BroadCastKeyboards.back_to_broadcast()
		)
		return
	
	text = "📜 <b>Последние рассылки:</b>\n\n"
	for broadcast in broadcasts:
		text += (
			f"ID: {broadcast.id}\n"
			f"Дата: {broadcast.sent_at.strftime('%d.%m.%Y %H:%M')}\n"
			f"Успешно: {broadcast.success_count}/{broadcast.total_users}\n\n"
		)
	
	await callback.message.edit_text(
		text,
		reply_markup=BroadCastKeyboards.broadcast_history(broadcasts)
	)
	await callback.answer()


# Детали рассылки
@router.callback_query(F.data.startswith("broadcast_details:"))
async def show_broadcast_details(
		callback: types.CallbackQuery,
		services: Services
):
	"""Детали конкретной рассылки"""
	broadcast_id = int(callback.data.split(":")[1])
	broadcast = await services.broadcast.get_broadcast_by_id(broadcast_id)
	
	if not broadcast:
		await callback.answer("❌ Рассылка не найдена", show_alert=True)
		return
	
	text = await services.broadcast.format_broadcast_stats(broadcast)
	
	await callback.message.edit_text(
		text,
		reply_markup=BroadCastKeyboards.broadcast_details(broadcast_id)
	)
	await callback.answer()


# Повторная рассылка
@router.callback_query(F.data.startswith("broadcast_repeat:"))
async def repeat_broadcast(
		callback: types.CallbackQuery,
		services: Services
):
	"""Повторная отправка рассылки"""
	search_broadcast_id = int(callback.data.split(":")[1])
	broadcast = await services.broadcast.get_broadcast_by_id(search_broadcast_id)
	
	if not broadcast:
		await callback.answer("❌ Рассылка не найдена", show_alert=True)
		return
	
	
	
	# Получаем список активных пользователей
	users = await services.user.get_users_for_notification()
	total_users = len(users)
	
	broadcast_id = await services.broadcast.save_broadcast(
		text=broadcast.text,
		media_type=broadcast.media_type,
		media_id=broadcast.media_id,
		buttons=broadcast.buttons,
		sent_by=callback.from_user.id,
		total_users=total_users
	)
	
	# Отправляем сообщение
	success = 0
	errors = 0
	
	for user in users:
		try:
			buttons = broadcast.buttons
			keyboard = None
			# Формируем клавиатуру
			if buttons:
				builder = InlineKeyboardBuilder()
				for btn in buttons:
					if btn.button_type == 'url':
						builder.button(text=btn.text, url=btn.value)
					else:
						builder.button(text=btn.text, callback_data=f"broadcast_textbtn:{broadcast_id}:{btn.id}")
				builder.adjust(1)  # 1 кнопка в ряд
				keyboard = builder.as_markup()
			
			if broadcast.media_type == 'photo':
				await callback.bot.send_photo(
					chat_id=user.user_id,
					photo=broadcast.media_id,
					caption=broadcast.text,
					reply_markup=keyboard
				)
			elif broadcast.media_type == 'video':
				await callback.bot.send_video(
					chat_id=user.user_id,
					video=broadcast.media_id,
					caption=broadcast.text,
					reply_markup=keyboard
				)
			elif broadcast.media_type == 'document':
				await callback.bot.send_document(
					chat_id=user.user_id,
					document=broadcast.media_id,
					caption=broadcast.text,
					reply_markup=keyboard
				)
			else:
				await callback.bot.send_message(
					chat_id=user.user_id,
					text=broadcast.text,
					reply_markup=keyboard
				)
			success += 1
		except Exception as e:
			logger.error(f"Ошибка отправки пользователю {user.user_id}: {e}")
			await services.user.set_notification_status(user.user_id, False)
			await services.user.ban_user(user.user_id)
			errors += 1
	
	# Обновляем статистику
	await services.broadcast.update_broadcast_stats(broadcast_id, success, errors)
	
	await callback.message.answer(
		f"✅ Повторная рассылка завершена!\n\n"
		f"• Успешно: {success}\n"
		f"• Ошибок: {errors}\n"
		f"• Всего получателей: {total_users}",
		reply_markup=BroadCastKeyboards.back_to_broadcast()
	)
	await callback.answer()
	
	
	

# Просмотр детально рассылки
@router.callback_query(F.data.startswith('broadcast_send'))
async def broadcast_send(callback: CallbackQuery, state: FSMContext, services: Services):
	
	search_broadcast_id = int(callback.data.split(":")[1])
	broadcast = await services.broadcast.get_broadcast_by_id(search_broadcast_id)
	
	if not broadcast:
		await callback.answer("❌ Рассылка не найдена", show_alert=True)
		return

	try:
		buttons = broadcast.buttons
		keyboard = None
		# Формируем клавиатуру
		if buttons:
			builder = InlineKeyboardBuilder()
			for btn in buttons:
				if btn.button_type == 'url':
					builder.button(text=btn.text, url=btn.value)
				else:
					builder.button(text=btn.text, callback_data=f"broadcast_textbtn:{search_broadcast_id}:{btn.id}")
			builder.button(text='Скрыть', callback_data='delete_this_message')
			builder.adjust(1)
			keyboard = builder.as_markup()
		
		if broadcast.media_type == 'photo':
			await callback.message.answer_photo(
				photo=broadcast.media_id,
				caption=broadcast.text,
				reply_markup=keyboard
			)
		elif broadcast.media_type == 'video':
			await callback.message.answer_video(
				video=broadcast.media_id,
				caption=broadcast.text,
				reply_markup=keyboard
			)
		elif broadcast.media_type == 'document':
			await callback.message.answer_document(
				document=broadcast.media_id,
				caption=broadcast.text,
				reply_markup=keyboard
			)
		else:
			await callback.message.answer(
				text=broadcast.text,
				reply_markup=keyboard
			)
	except Exception as e:
		logger.error(f"Ошибка отправки пользователю: {e}")
	
	await callback.answer()