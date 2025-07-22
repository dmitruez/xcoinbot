from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from ...keyboards.admin_keyboard import AdminKeyboards
from ...models import Admin
from ...services import Services
from ...states.admin_states import UserStates
from ...utils.paginator import Paginator


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

	admin = await services.admin.get_admin(message.from_user.id)
	access_level = admin.level if admin else 0

	user_info, is_admin, level = await services.user.format_user_info(user)
	await message.answer(
		"❌ Уведомления выключены ❌\n\n" + user_info,

		reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
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

	admin = await services.admin.get_admin(message.from_user.id)
	access_level = admin.level if admin else 0

	user_info, is_admin, level = await services.user.format_user_info(user)
	await message.answer(
		"✅ Уведомления включены ✅\n\n" + user_info,
		reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
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
		"Вы можете указать не весь @username/никнейм, бот подберет всех подходящих под запрос пользователей\n"
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
		admin = await services.admin.get_admin(message.from_user.id)
		access_level = admin.level if admin else 0

		# Если найден один пользователь - показываем подробную информацию
		user_info, is_admin, level = await services.user.format_user_info(users[0])
		await message.answer(
			user_info,
			reply_markup=AdminKeyboards.profile_menu(users[0], is_admin, level, access_level=access_level)
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
	await state.set_state(UserStates.WAITING_ID)


@router.message(F.text.regexp(r'^\d+$'), UserStates.WAITING_ID)
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

	admin = await services.admin.get_admin(message.from_user.id)
	access_level = admin.level if admin else 0

	if not user:
		await message.answer("❌ Пользователь не найден")
		return

	user_info, is_admin, level = await services.user.format_user_info(user)
	await message.answer(
		user_info,
		reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
	)


# ДОРАБОТАТЬ ЕСЛИ ПОНАДОБИТСЯ
@router.callback_query(F.data == "admin_users_list")
async def get_users_list(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Показ всех пользователей"""
	await callback.answer("❌ Пока в разработке ❌")
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
#
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
#
# 		reply_markup=AdminKeyboards.profile_menu(user)
# 	)



@router.callback_query(F.data.startswith("admin_ban_"))
async def ban_user(callback: types.CallbackQuery, services: Services, admin: Admin):
	"""Блокировка пользователя"""
	user_id = int(callback.data.split("_")[2])
	access_level = admin.level if admin else 0

	if await services.user.set_notification_status(user_id, False):
		user = await services.user.get_user_by_id(user_id)
		user_info, is_admin, level = await services.user.format_user_info(user)
		await callback.message.edit_text(
			"❌ Уведомления выключены ❌\n\n" + user_info,
			reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
		)
	else:
		await callback.answer("❌ Ошибка блокировки уведомлений", show_alert=True)


@router.callback_query(F.data.startswith("admin_unban_"))
async def unban_user(callback: types.CallbackQuery, services: Services, admin: Admin):
	"""Разблокировка пользователя"""
	user_id = int(callback.data.split("_")[2])
	access_level = admin.level if admin else 0

	if await services.user.set_notification_status(user_id, True):
		user = await services.user.get_user_by_id(user_id)
		user_info, is_admin, level = await services.user.format_user_info(user)
		await callback.message.edit_text(
			"✅ Уведомления включены ✅\n\n" + user_info,
			reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
		)
	else:
		await callback.answer("❌ Ошибка разблокировки увеломлений", show_alert=True)


@router.callback_query(F.data.startswith("admin_grant_"))
async def grant_admin_handler(callback: types.CallbackQuery, services: Services, admin: Admin):
	"""Назначение пользователя администратором"""
	user_id = int(callback.data.split("_")[2])
	user = await services.user.get_user_by_id(user_id)

	# Проверяем права текущего админа
	access_level = admin.level if admin else 0
	if access_level < 2:
		await callback.answer("❌ Недостаточно прав!", show_alert=True)
		return

	new_admin = Admin(
		user_id=user_id,
		username=user.username,
		full_name=user.full_name,
		level=1
	)

	if await services.admin.add_admin(new_admin):
		await callback.answer("✅ Пользователь назначен администратором!")

		# Обновляем сообщение
		user_info, is_admin, level = await services.user.format_user_info(user)

		await callback.message.edit_text(
			user_info,
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
		)
	else:
		await callback.answer("❌ Ошибка назначения админа", show_alert=True)


@router.callback_query(F.data.startswith("admin_revoke_"))
async def revoke_admin_handler(callback: types.CallbackQuery, services: Services, admin: Admin):
	"""Снятие прав администратора"""
	user_id = int(callback.data.split("_")[2])


	# Проверяем права текущего админа
	access_level = admin.level if admin else 0
	if access_level < 2:
		await callback.answer("❌ Недостаточно прав!", show_alert=True)
		return

	if await services.admin.remove_admin(user_id):
		await callback.answer("✅ Админские права отозваны!")

		# Обновляем сообщение
		user = await services.user.get_user_by_id(user_id)
		user_info, is_admin, level = await services.user.format_user_info(user)

		await callback.message.edit_text(
			user_info,
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
		)
	else:
		await callback.answer("❌ Ошибка отзыва прав", show_alert=True)


@router.callback_query(F.data.startswith("admin_setlevel_"))
async def set_admin_level_handler(callback: types.CallbackQuery, services: Services, admin: Admin):
	"""Установка уровня администратора"""
	parts = callback.data.split("_")
	user_id = int(parts[2])
	level = int(parts[3])

	# Проверяем права текущего админа
	access_level = admin.level if admin else 0
	if access_level < 2:
		await callback.answer("❌ Недостаточно прав!", show_alert=True)
		return


	if await services.admin.update_admin_level(user_id, level):
		await callback.answer(f"✅ Уровень админа установлен: {level}")

		# Обновляем сообщение
		user = await services.user.get_user_by_id(user_id)
		user_info, is_admin, level = await services.user.format_user_info(user)

		await callback.message.edit_text(
			user_info,
			parse_mode=ParseMode.HTML,
			reply_markup=AdminKeyboards.profile_menu(user, is_admin, level, access_level=access_level)
		)
	else:
		await callback.answer("❌ Ошибка изменения уровня", show_alert=True)