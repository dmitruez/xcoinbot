from aiogram import Router, types, F, Bot
from aiogram.enums import ParseMode, ChatType
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatMemberUpdated

from xcoinbot.bot.keyboards.admin_keyboard import AdminKeyboards
from xcoinbot.bot.models import Channel
from xcoinbot.bot.services import Services
from xcoinbot.bot.states.admin_states import ChannelsStates
from xcoinbot.bot.utils.paginator import Paginator


router = Router(name=__name__)


@router.callback_query(F.data == "admin_channels")
async def admin_channels(callback: types.CallbackQuery, state: FSMContext):
	"""Управление каналами"""
	await callback.message.edit_text(
		"📢 <b>Управление каналами</b>\n\n"
		"Выберите действие:",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.channels_menu()
	)
	await state.set_state(ChannelsStates.CHANNELS)
	await callback.answer()


@router.callback_query(F.data == "admin_change_main")
async def start_select_main_channel(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Начало выбора основного канала"""
	channels = await services.channel.get_channel_list()
	if not channels:
		await callback.answer("ℹ Нет доступных каналов", show_alert=True)
		return

	paginator = Paginator(channels, per_page=6)
	page = paginator.get_page(1)

	buttons = [
		(f"📢 {ch.title}", f"select_main_{ch.channel_id}")
		for ch in page.items
	]

	main_channel = await services.channel.get_main_channel()
	if main_channel:
		await callback.message.edit_text(
			"🟢 <b>Выберите основной канал:</b> 🟢\n\n"
			f"Текущий канал: <a src='{main_channel.link}'>{main_channel.title}</a>\n\n",
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards().channels_list(
				buttons,
				page.page,
				page.total_pages,
				"main"
			)
		)
	else:
		await callback.message.edit_text(
			"🟢 <b>Выберите основной канал:</b> 🟢\n\n"
			"Текущий канал: <b>НЕ УСТАНОВЛЕН</b>",
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards().channels_list(
				buttons,
				page.page,
				page.total_pages,
				"main"
			)
		)
	await state.set_state(ChannelsStates.EDIT_MAIN_CHANNEL)
	await callback.answer()


@router.callback_query(F.data.startswith("select_main_"))
async def set_main_channel(callback: types.CallbackQuery, services: Services):
	"""Установка основного канала"""
	channel_id = int(callback.data.split("_")[2])
	channel = await services.channel.get_channel(channel_id)

	if not channel:
		await callback.answer("❌ Канал не найден", show_alert=True)
		return

	await services.channel.set_main_channel(channel_id)
	await callback.message.edit_text(
		f"✅ Основной канал установлен: <b>{channel.title}</b>",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.back_to_main()
	)
	await callback.answer()


@router.callback_query(F.data == "admin_change_backup")
async def start_select_backup_channel(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Начало выбора резервного канала"""
	channels = await services.channel.get_channel_list()
	if not channels:
		await callback.answer("ℹ Нет доступных каналов", show_alert=True)
		return

	paginator = Paginator(channels, per_page=6)
	page = paginator.get_page(1)

	buttons = [
		(f"📢 {ch.title}", f"select_backup_{ch.channel_id}")
		for ch in page.items
	]

	backup_channel = await services.channel.get_backup_channel()
	if backup_channel:
		await callback.message.edit_text(
			"🔶 <b>Выберите резервный канал:</b> 🔶\n\n"
			f"Текущий канал: <a src='{backup_channel.link}'>{backup_channel.title}</a>",
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards().channels_list(
				buttons,
				page.page,
				page.total_pages,
				"backup"
			)
		)
	else:
		await callback.message.edit_text(
			"🔶 <b>Выберите резервный канал:</b> 🔶\n\n"
			f"Текущий канал: <b>НЕ УСТАНОВЛЕН</b>",
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards().channels_list(
				buttons,
				page.page,
				page.total_pages,
				"backup"
			)
		)
	await state.set_state(ChannelsStates.EDIT_BACKUP_CHANNEL)
	await callback.answer()


@router.callback_query(F.data.startswith("select_backup_"))
async def set_backup_channel(callback: types.CallbackQuery, services: Services):
	"""Установка резервного канала"""
	channel_id = int(callback.data.split("_")[2])
	channel = await services.channel.get_channel(channel_id)

	if not channel:
		await callback.answer("❌ Канал не найден", show_alert=True)
		return

	await services.channel.set_backup_channel(channel_id)
	await callback.message.edit_text(
		f"✅ Резервный канал установлен: <b>{channel.title}</b>",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.back_to_main()
	)
	await callback.answer()


@router.callback_query(F.data.regexp(r"^(main|backup)_page_\d+$"))
async def paginate_channels(callback: types.CallbackQuery, services: Services, state: FSMContext):
	"""Обработка пагинации"""
	parts = callback.data.split("_")
	prefix = parts[0]
	page_num = int(parts[2])

	channels = await services.channel.get_channel_list()
	paginator = Paginator(channels, per_page=6)
	page = paginator.get_page(page_num)

	if prefix == "main":
		buttons = [(f"📢 {ch.title}", f"select_main_{ch.channel_id}") for ch in page.items]
		await state.set_state(ChannelsStates.EDIT_MAIN_CHANNEL)
		text = "🟢 <b>Выберите основной канал:</b> 🟢"
	else:
		buttons = [(f"📢 {ch.title}", f"select_backup_{ch.channel_id}") for ch in page.items]
		await state.set_state(ChannelsStates.EDIT_BACKUP_CHANNEL)
		text = "🔶 <b>Выберите резервный канал:</b> 🔶"

	await callback.message.edit_text(
		text,
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards().channels_list(
			buttons,
			page.page,
			page.total_pages,
			prefix
		)
	)
	await callback.answer()


@router.my_chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def handle_bot_added_to_channel(update: ChatMemberUpdated, state: FSMContext, bot: Bot, services: Services):
	"""Обработка добавления бота в канал или группу"""
	# Проверяем, что это именно канал (не группа или чат)
	if update.chat.type != ChatType.CHANNEL:
		return

	# Проверяем, что бота добавил именно администратор бота
	admin = await services.admin.get_admin(update.from_user.id)
	if admin.level < 2:
		return

	# Проверяем, что бота именно добавили (не удалили или другие изменения)
	channel = Channel(
		channel_id=update.chat.id,
		title=update.chat.title,
		username=update.chat.username,
		is_main=False,
		is_backup=False
	)

	# Проверяем, есть ли уже канал в базе
	existing_channel = await services.channel.get_channel(channel.channel_id)
	if not existing_channel:
		await services.channel.add_new_channel(channel)
	await bot.send_message(
		chat_id=2048360747,
		text=f"🤖 Вы добавили бота в канал!\n"
			 f"Название: {channel.title}\n"
			 f"ID: {channel.channel_id}\n\n"
			 f"<b>Теперь кликни на кнопку и отправь пригласительную ссылку для этого чата 👇</b>",
		reply_markup=AdminKeyboards.send_link(channel_id=channel.channel_id)
	)


@router.callback_query(F.data.startswith("admin_link_channel_"))
async def add_link(callback: types.CallbackQuery, state: FSMContext, services: Services):
	channel_id = int(callback.data.split('_')[3])
	channel = await services.channel.get_channel(channel_id)
	await callback.message.edit_reply_markup(reply_markup=AdminKeyboards.send_link(waiting=True))
	await state.update_data(channel=channel, clbk_message=callback.message)
	await state.set_state(ChannelsStates.ADD_LINK)


@router.message(F.text, ChannelsStates.ADD_LINK)
async def adding_channel_link(message: types.Message, state: FSMContext, services: Services):
	data = await state.get_data()
	channel: Channel = data["channel"]
	clbk_message = data["clbk_message"]
	link = message.text
	channel.link = link
	await services.channel.update_channel(channel)
	await message.delete()
	await clbk_message.edit_reply_markup(reply_markup=AdminKeyboards.send_link(success=True))
	await state.clear()


@router.my_chat_member(ChatMemberUpdatedFilter(LEAVE_TRANSITION))
async def leave_channel(update: ChatMemberUpdated, services: Services):
	"""Обработчик изменения статуса бота в чате/канале"""
	# Нас интересуют только каналы
	if update.chat.type != ChatType.CHANNEL:
		return

	new_status = update.new_chat_member.status

	# Канал был удален (бота удалили или канал исчез)
	if new_status in ('left', 'kicked'):
		channel = await services.channel.get_channel(update.chat.id)
		if not channel:
			return

		_, super_admins = await services.admin.list_admins()
		# Если это был основной канал
		if channel.is_main:
			backup_channel = await services.channel.get_backup_channel()
			if backup_channel:
				# Автоматически делаем резервный канал основным
				await services.channel.set_main_channel(backup_channel.channel_id)

				# Отправляем уведомления пользователям
				data = await services.notification.notify_channel_change(
					new_channel=backup_channel
				)

				for admin in super_admins:
					try:
						await update.bot.send_message(
							admin.user_id,
							f"⚠️ Основной канал {channel.title} был удален!\n"
							f"Автоматически назначен новый основной канал: {backup_channel.title}\n"
							f"Уведомления отправлены {data['success']} пользователям\n"
							f"Пользователи которым не удалось отправить уведомления: {data['failures']}"
						)
					except Exception:
						continue

			# Уведомляем админов
			# for admin_id in Config.DEVELOPERS_IDS:
			# 	try:
			# 		await update.bot.send_message(
			# 			admin_id,
			# 			f"⚠️ Основной канал {channel.title} был удален!\n"
			# 			f"Автоматически назначен новый основной канал: {backup_channel.title}\n"
			# 			f"Уведомления отправлены {data['success']} пользователям\n"
			# 			f"Пользователи которым не удалось отправить уведомления: {data['failures']}"
			# 		)
			# 	except Exception:
			# 		continue

			else:
				# Нет резервного канала - срочное уведомление админам
				for admin in super_admins:
					try:
						await update.bot.send_message(
							admin.user_id,
							f"🚨 КРИТИЧЕСКОЕ СОБЫТИЕ!\n"
							f"Основной канал {channel.title} был удален, "
							f"а резервный канал не настроен!\n"
							f"Немедленно настройте новый канал!"
						)
					except Exception:
						continue

			# for admin_id in Config.DEVELOPERS_IDS:
			# 	try:
			# 		await update.bot.send_message(
			# 			admin_id,
			# 			f"🚨 КРИТИЧЕСКОЕ СОБЫТИЕ!\n"
			# 			f"Основной канал {channel.title} был удален, "
			# 			f"а резервный канал не настроен!\n"
			# 			f"Немедленно настройте новый канал!"
			# 		)
			# 	except Exception:
			# 		continue

		# Удаляем информацию о канале из БД
		await services.channel.delete_channel(channel)
