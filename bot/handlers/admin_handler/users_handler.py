from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from xcoinbot.bot.keyboards.admin_keyboard import AdminKeyboards
from xcoinbot.bot.services import Services
from xcoinbot.bot.states.admin_states import UserStates
from xcoinbot.bot.utils.paginator import Paginator


router = Router(name=__name__)

@router.message(Command('ban'))
async def admin_ban_user(message: types.Message,  command: CommandObject, services: Services):
	"""Бан пользователя"""
	if not command.args:
		await message.answer(
			"Используйте команду /ban вместе с ID\n\n"
			"Пример: /ban 123456"
		)
		return
	if not command.args.isdigit():
		await message.delete()
		await message.answer(
			"❌ ID должен содержать только цифры"
		)
		return
	user_id = int(command.args)
	await services.user.set_notification_status(user_id, False)
	user = await services.user.get_user_by_id(user_id)

	user_info = await services.user.format_user_info(user)
	await message.answer(
		"❌ Уведомления выключены ❌\n\n" + user_info,
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.profile_menu(user)
	)


@router.message(Command('unban'))
async def admin_unban_user(message: types.Message, command: CommandObject, services: Services):
	"""Разбан пользователя"""
	if not command.args:
		await message.answer(
			"Используйте команду /unban вместе с ID\n\n"
			"Пример: /ban 123456"
		)
		return
	if not command.args.isdigit():
		await message.delete()
		await message.answer(
			"❌ ID должен содержать только цифры"
		)
		return
	user_id = int(command.args)
	await services.user.set_notification_status(user_id, True)
	user = await services.user.get_user_by_id(user_id)

	user_info = await services.user.format_user_info(user)
	await message.answer(
		"✅ Уведомления включены ✅\n\n" + user_info,
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.profile_menu(user)
	)




@router.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery, state: FSMContext):
	"""Управление пользователями"""
	await callback.message.edit_text(
		"👤 <b>Управление пользователями</b>\n\n"
		"Выберите действие:",
		reply_markup=AdminKeyboards.users_menu()
	)
	await state.set_state(UserStates.USERS)
	await callback.answer()


@router.callback_query(F.data == "admin_search_user", UserStates.USERS)
async def admin_search_user(callback: types.CallbackQuery):
	"""Меню для поиска пользователя"""
	await callback.message.edit_text(
		"👤 <b>Поиск пользователей</b>\n\n"
		"Вы можете указать не весь @username/никнейм, бот подберет всех подходящих под запрос пользователей"
		"Выберите действие:",
		reply_markup=AdminKeyboards.search_menu()
	)

	await callback.answer()


@router.callback_query(F.data == "admin_search_username")
async def search_by_username_start(callback: types.CallbackQuery, state: FSMContext):
	"""Начало поиска по username"""
	await callback.message.edit_text(
		"🔍 <b>Поиск по username</b>\n\n"
		"Введите часть username (без @):",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.cancel_search()
	)
	await state.set_state(UserStates.WAITING_QUERY)
	await state.update_data(search_type="username")
	await callback.answer()


@router.callback_query(F.data == "admin_search_nickname")
async def search_by_nickname_start(callback: types.CallbackQuery, state: FSMContext):
	"""Начало поиска по nickname"""
	await callback.message.edit_text(
		"🔍 <b>Поиск по имени/фамилии</b>\n\n"
		"Введите часть имени или фамилии:",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.cancel_search()
	)
	await state.set_state(UserStates.WAITING_QUERY)
	await state.update_data(search_type="nickname")
	await callback.answer()


@router.callback_query(F.data == "admin_search_id")
async def search_by_id_start(callback: types.CallbackQuery, state: FSMContext):
	"""Начало поиска по ID"""
	await callback.message.edit_text(
		"🔍 <b>Поиск по ID</b>\n\n"
		"Введите ID пользователя:",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.cancel_search()
	)
	await state.set_state(UserStates.WAITING_QUERY)
	await state.update_data(search_type="id")
	await callback.answer()


@router.message(UserStates.WAITING_QUERY)
async def handle_search_query(message: types.Message, state: FSMContext, services: Services):
	"""Обработка поискового запроса"""
	data = await state.get_data()
	search_type = data.get("search_type")
	query = message.text.strip()

	if not query:
		await message.answer("❌ Запрос не может быть пустым")
		return

	# Выполняем поиск
	users = await services.user.search_users(search_type, query)

	if not users:
		await message.answer("🔍 Пользователи не найдены")
		await state.clear()
		return

	# Отправляем результаты
	if len(users) == 1:
		# Если найден один пользователь - показываем подробную информацию
		user_info = await services.user.format_user_info(users[0])
		await message.answer(
			user_info,
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards.profile_menu(users[0])
		)
	else:
		# Если несколько пользователей - показываем список
		users_list = "\n".join(
			f"{i + 1}. @{u.username} - {u.full_name} (ID: <code>{u.user_id}</code>)"
			for i, u in enumerate(users[:10])  # Ограничиваем 10 результатами
		)
		await message.answer(
			f"🔍 Найдено пользователей: {len(users)}\n\n"
			f"{users_list}\n\n"
			"Для просмотра подробностей отправьте ID пользователя.",
			reply_markup=AdminKeyboards.back_to_search()
		)
	await state.set_state(UserStates.WAITING_QUERY)


@router.message(F.text.regexp(r'^\d+$'), UserStates.WAITING_QUERY)
async def handle_user_id_input(message: types.Message, services: Services):
	"""Обработка ввода ID пользователя"""
	if not message.text.isdigit():
		await message.delete()
		await message.answer(
			f"❌ Укажите верный id"
		)
		return
	user_id = int(message.text)
	user = await services.user.get_user_by_id(user_id)

	if not user:
		await message.answer("❌ Пользователь не найден")
		return

	user_info = await services.user.format_user_info(user)
	await message.answer(
		user_info,
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.profile_menu(user)
	)


# ДОРАБОТАТЬ ЕСЛИ ПОНАДОБИТСЯ
# @router.callback_query(F.data == "admin_users_list")
# async def get_users_list(callback: types.CallbackQuery, state: FSMContext, services: Services):
# 	"""Показ всех пользователей"""
# 	users = await services.user.users_list()
#
# 	if not users:
# 		await callback.answer("ℹ Нет доступных пользователей", show_alert=True)
# 		return
#
# 	paginator = Paginator(users, per_page=6)
# 	page = paginator.get_page(1)
#
# 	buttons = [
# 		(f" {us.full_name if us.full_name else }", f"select_{us.user_id}")
# 		for us in page.items
# 	]
#
# 	await callback.message.edit_text(
# 		"🟢 <b>Выберите пользователя:</b> 🟢",
# 		parse_mode=ParseMode.HTML,
# 		reply_markup=AdminKeyboards().users_list(
# 			users=buttons,
# 			current_page=page.page,
# 			total_pages=page.total_pages,
# 			prefix='user'
# 		)
# 	)
# 	await state.set_state(UserStates.CHOOSE_USER)
# 	await callback.answer()
#
#
# @router.callback_query(F.data.startswith("select_"))
# async def get_user_profile(callback: types.CallbackQuery, services: Services):
# 	"""Просмотр профиля пользователя"""
# 	user_id = int(callback.data.split("_")[1])
# 	user = await services.user.get_user_by_id(user_id)
#
# 	if not user:
# 		await callback.answer("❌ Пользователь не найден", show_alert=True)
# 		return
#
# 	user_link = f"<a href='tg://user?id={user_id}'>{user.full_name}</a>\n"
# 	await callback.message.answer(
# 		f"👤 Пользователь: @{user.username if user.username else user_link}\n"
# 		f"🆔 ID: <code>{user_id}</code>\n"
# 		f"👤 Имя: {user.full_name}\n"
# 		f"🔒 Статус: {'🟢 Активен' if user.is_active else '🔴 Заблокирован'}\n"
# 		f"Уведомления: {'🟢 Включены' if user.should_notify else '🔴 Выключены'}",
# 		parse_mode=ParseMode.HTML,
# 		reply_markup=AdminKeyboards.profile_menu(user)
# 	)



@router.callback_query(F.data.startswith("admin_ban_"))
async def ban_user(callback: types.CallbackQuery, services: Services):
	"""Блокировка пользователя"""
	user_id = int(callback.data.split("_")[2])

	if await services.user.set_notification_status(user_id, False):
		user = await services.user.get_user_by_id(user_id)
		user_info = await services.user.format_user_info(user)
		await callback.message.edit_text(
			"❌ Уведомления выключены ❌\n\n" + user_info,
			reply_markup=AdminKeyboards.profile_menu(user)
		)
	else:
		await callback.answer("❌ Ошибка блокировки уведомлений", show_alert=True)


@router.callback_query(F.data.startswith("admin_unban_"))
async def unban_user(callback: types.CallbackQuery, services: Services):
	"""Разблокировка пользователя"""
	user_id = int(callback.data.split("_")[2])

	if await services.user.set_notification_status(user_id, True):
		user = await services.user.get_user_by_id(user_id)
		user_info = await services.user.format_user_info(user)
		await callback.message.edit_text(
			"✅ Уведомления включены ✅\n\n" + user_info,
			reply_markup=AdminKeyboards.profile_menu(user)
		)
	else:
		await callback.answer("❌ Ошибка разблокировки увеломлений", show_alert=True)
