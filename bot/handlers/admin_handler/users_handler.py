from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext

from xcoinbot.bot.keyboards.admin_keyboard import AdminKeyboards
from xcoinbot.bot.services import Services
from xcoinbot.bot.states.admin_states import UserStates
from xcoinbot.bot.utils.paginator import Paginator


router = Router(name=__name__)


@router.callback_query(F.data == "admin_users")
async def admin_users(callback: types.CallbackQuery, state: FSMContext):
	"""Управление пользователями"""
	await callback.message.edit_text(
		"👤 <b>Управление пользователями</b>\n\n"
		"Выберите действие:",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.users_menu()
	)
	await state.set_state(UserStates.USERS)
	await callback.answer()


@router.callback_query(F.data == "admin_ban")
async def admin_ban_menu(callback: types.CallbackQuery):
	"""Меню бана/разбана"""
	await callback.message.edit_text(
		"🔨 <b>Управление блокировками</b>\n\n"
		"Отправьте ID пользователя для блокировки/разблокировки:",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.back_to_main()
	)
	await callback.answer()


@router.callback_query(F.data == "admin_users_list")
async def get_users_list(callback: types.CallbackQuery, state: FSMContext, services: Services):
	"""Показ всех пользователей"""
	users = await services.user.users_list()

	if not users:
		await callback.answer("ℹ Нет доступных пользователей", show_alert=True)
		return

	paginator = Paginator(users, per_page=6)
	page = paginator.get_page(1)

	buttons = [
		(f" {us.full_name}", f"select_{us.user_id}")
		for us in page.items
	]

	await callback.message.edit_text(
		"🟢 <b>Выберите пользователя:</b> 🟢",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards().users_list(
			users=buttons,
			current_page=page.page,
			total_pages=page.total_pages,
			prefix='user'
		)
	)
	await state.set_state(UserStates.CHOOSE_USER)
	await callback.answer()


@router.callback_query(F.data.startswith("select_"))
async def get_user_profile(callback: types.CallbackQuery, services: Services):
	"""Просмотр профиля пользователя"""
	user_id = int(callback.data.split("_")[1])
	user = await services.user.get_user(user_id)

	if not user:
		await callback.answer("❌ Пользователь не найден", show_alert=True)
		return

	user_link = f"<a href='tg://user?id={user_id}'>{user.full_name}</a>\n"
	await callback.message.answer(
		f"👤 Пользователь: @{user.username if user.username else user_link}\n"
		f"🆔 ID: <code>{user_id}</code>\n"
		f"👤 Имя: {user.full_name}\n"
		f"🔒 Статус: {'🟢 Активен' if user.is_active else '🔴 Заблокирован'}\n"
		f"Уведомления: {'🟢 Включены' if user.is_active else '🔴 Выключены'}",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.profile_menu(user)
	)


@router.message(F.text.regexp(r'^\d+$'), UserStates.USERS)
async def process_user_id(message: types.Message, state: FSMContext, services: Services):
	"""Обработка ID пользователя для бана/разбана"""
	user_id = int(message.text)

	user = await services.user.get_user(user_id)
	if not user:
		return await message.answer("❌ Пользователь не найден")

	await state.update_data(target_user_id=user_id)
	user_link = f"<a href='tg://user?id={user_id}'>{user.full_name}</a>\n"
	await message.answer(
		f"👤 Пользователь: {user.username if user.username else user_link}"
		f"🆔 ID: <code>{user_id}</code>\n"
		f"👤 Имя: {user.full_name}\n"
		f"🔒 Статус: {'🟢 Активен' if user.is_active else '🔴 Заблокирован'}",
		parse_mode=ParseMode.HTML,
		reply_markup=AdminKeyboards.ban_menu(user_id, user.is_banned)
	)


@router.callback_query(F.data.startswith("admin_ban_"))
async def ban_user(callback: types.CallbackQuery, services: Services):
	"""Блокировка пользователя"""
	user_id = int(callback.data.split("_")[2])

	if await services.user.ban_user(user_id):
		user = await services.user.get_user(user_id)
		await callback.answer(f"✅ Пользователь {user_id} заблокирован")
		await callback.message.edit_reply_markup(
			reply_markup=AdminKeyboards.profile_menu(user)
		)
	else:
		await callback.answer("❌ Ошибка блокировки", show_alert=True)


@router.callback_query(F.data.startswith("admin_unban_"))
async def unban_user(callback: types.CallbackQuery, services: Services):
	"""Разблокировка пользователя"""
	user_id = int(callback.data.split("_")[2])

	if await services.user.unban_user(user_id):
		await callback.answer(f"✅ Пользователь {user_id} разблокирован")
		await callback.message.edit_reply_markup(
			reply_markup=AdminKeyboards.ban_menu(user_id, False)
		)
	else:
		await callback.answer("❌ Ошибка разблокировки", show_alert=True)
