import html

from aiogram import F, Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from ..keyboards.user_keyboard import (
	BACK_TO_MENU_BUTTON,
	CONTACT_ADMINS_BUTTON,
	USER_REPLY_CALLBACK_PREFIX,
	UserKeyboards,
)
from ..services import Services
from ..states.base_states import UserChatStates


router = Router(name=__name__)


async def _get_active_user(message: types.Message, services: Services):
	"""Проверяем, что пользователь прошёл капчу и не является админом"""
	if message.text and message.text.startswith('/'):
		return None

	admin = await services.admin.get_admin(message.from_user.id)
	if admin:
		return None

	user = await services.user.get_user_by_id(message.from_user.id)
	if not user or not user.captcha_passed:
		return None

	return user


@router.message(StateFilter(None), F.text == CONTACT_ADMINS_BUTTON)
async def start_user_dialog(message: types.Message, state: FSMContext, services: Services):
	user = await _get_active_user(message, services)
	if not user:
		return

	await state.set_state(UserChatStates.WAITING_MESSAGE)
	await state.update_data(reply_to_admin_id=None)
	await message.answer(
		"✏️ <b>Напишите сообщение администрации</b>\n\n"
		"Опишите ваш вопрос максимально подробно.",
		reply_markup=UserKeyboards.chat_cancel()
	)


@router.callback_query(F.data.startswith(f"{USER_REPLY_CALLBACK_PREFIX}_"))
async def reply_to_admin(callback: types.CallbackQuery, state: FSMContext, services: Services):
	try:
		admin_id = int(callback.data.split('_')[-1])
	except (ValueError, IndexError):
		await callback.answer("❌ Некорректный администратор", show_alert=True)
		return

	admin = await services.admin.get_admin(admin_id)
	if not admin:
		await callback.answer("❌ Администратор не найден", show_alert=True)
		return

	user = await services.user.get_user_by_id(callback.from_user.id)
	if not user or not user.captcha_passed:
		await callback.answer("⚠️ Доступно только после прохождения капчи", show_alert=True)
		return

	await state.set_state(UserChatStates.WAITING_MESSAGE)
	await state.update_data(reply_to_admin_id=admin.user_id)
	await callback.message.answer(
		"✏️ <b>Напишите ответ администратору</b>\n\n"
		+ f"Вы отвечаете: {html.escape(admin.full_name)} "
		+ f"(ID: <code>{admin.user_id}</code>)",
		reply_markup=UserKeyboards.chat_cancel()
	)
	await callback.answer()


@router.message(UserChatStates.WAITING_MESSAGE, F.text == BACK_TO_MENU_BUTTON)
async def cancel_user_dialog(message: types.Message, state: FSMContext):
	await state.clear()
	await message.answer("📋 Главное меню", reply_markup=UserKeyboards.main_menu())


@router.message(UserChatStates.WAITING_MESSAGE, F.text)
async def forward_user_message(message: types.Message, state: FSMContext, services: Services):
	user = await _get_active_user(message, services)
	if not user:
		await state.clear()
		return

	text = message.text.strip()
	if not text:
		await message.answer("❌ Сообщение не может быть пустым")
		return

	data = await state.get_data()
	target_admin_id = data.get('reply_to_admin_id')

	saved = await services.chat.save_user_message(user.user_id, text)
	if not saved:
		await message.answer("❌ Не удалось отправить сообщение, попробуйте позже")
		return

	await services.chat.notify_admins_about_user_message(user, text, target_admin_id=target_admin_id)

	await state.clear()
	await message.answer("✅ Сообщение отправлено администрации", reply_markup=UserKeyboards.main_menu())


@router.message(UserChatStates.WAITING_MESSAGE)
async def handle_unsupported_content(message: types.Message):
	await message.answer("⚠️ Можно отправлять только текстовое сообщение")


@router.message(StateFilter(None), F.text)
async def remind_chat_button(message: types.Message, services: Services):
	user = await _get_active_user(message, services)
	if not user:
		return

	await message.answer(
		"ℹ️ Чтобы написать администрации, используйте кнопку"
		" «Написать админам» в меню.",
		reply_markup=UserKeyboards.main_menu()
	)
