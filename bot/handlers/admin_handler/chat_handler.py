import html
from typing import List

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from ...keyboards.admin_keyboard import AdminKeyboards
from ...models import Admin, ChatDialog
from ...services import Services
from ...states.admin_states import ChatStates


router = Router(name=__name__)


def _format_dialogs(title: str, dialogs: List[ChatDialog]) -> str:
	if not dialogs:
		return title + "\n\n📭 Здесь пока пусто."

	lines = [title, ""]
	for index, dialog in enumerate(dialogs, start=1):
		username = f"@{dialog.username}" if dialog.username else "без username"
		preview = dialog.last_message.replace('\n', ' ')
		if len(preview) > 60:
			preview = preview[:57] + "..."
		lines.append(
			f"{index}. <b>{html.escape(dialog.full_name)}</b>"
			f" ({username})\n"
			f"Последнее: {dialog.last_at.strftime('%d.%m %H:%M')}"
		)
		if dialog.unread_count:
			lines.append(f"Непрочитанных: <b>{dialog.unread_count}</b>")
		lines.append(f"Сообщение: <i>{html.escape(preview)}</i>\n")
	return "\n".join(lines)


async def _format_history(services: Services, user_id: int) -> str:
	user = await services.user.get_user_by_id(user_id)
	header_name = html.escape(user.full_name if user else str(user_id))
	header_username = f" (@{user.username})" if user and user.username else ""
	messages = await services.chat.get_history(user_id)

	lines = [
		f"💬 <b>Диалог с {header_name}</b>{header_username}",
		f"ID: <code>{user_id}</code>",
		""
	]

	if not messages:
		lines.append("Сообщений ещё не было.")
		return "\n".join(lines)

	admin_names: dict[int, str] = {}
	for message in messages:
		time_label = message.created_at.strftime('%d.%m %H:%M')
		if message.sender == 'user':
			sender = "👤 Пользователь"
		else:
			if message.admin_id and message.admin_id not in admin_names:
				admin = await services.admin.get_admin(message.admin_id)
				admin_names[message.admin_id] = admin.full_name if admin else f"Админ {message.admin_id}"
			sender = f"👑 {admin_names.get(message.admin_id, 'Администратор')}"
		text = html.escape(message.message)
		lines.append(f"<code>{time_label}</code> {sender}\n{text}\n")

	return "\n".join(lines)


@router.callback_query(F.data == "admin_messages")
async def open_messages_menu(callback: types.CallbackQuery, state: FSMContext):
	await state.set_state(ChatStates.LIST)
	await callback.message.edit_text(
		"💬 <b>Диалоги с пользователями</b>\n\nВыберите раздел:",
		reply_markup=AdminKeyboards.messages_menu()
	)
	await callback.answer()


@router.callback_query(F.data == "admin_messages_unread")
async def show_unread_dialogs(callback: types.CallbackQuery, services: Services):
	dialogs = await services.chat.get_unread_dialogs()
	text = _format_dialogs("📥 <b>Непрочитанные диалоги</b>", dialogs)
	markup = AdminKeyboards.dialogs_list(dialogs, "admin_messages_open") if dialogs else AdminKeyboards.messages_menu()
	await callback.message.edit_text(text, reply_markup=markup)
	await callback.answer()


@router.callback_query(F.data == "admin_messages_recent")
async def show_recent_dialogs(callback: types.CallbackQuery, services: Services):
	dialogs = await services.chat.get_recent_dialogs()
	text = _format_dialogs("🕘 <b>Последние диалоги</b>", dialogs)
	markup = AdminKeyboards.dialogs_list(dialogs, "admin_messages_open") if dialogs else AdminKeyboards.messages_menu()
	await callback.message.edit_text(text, reply_markup=markup)
	await callback.answer()


@router.callback_query(F.data.startswith("admin_messages_open_"))
async def open_dialog(callback: types.CallbackQuery, state: FSMContext, services: Services):
	try:
		user_id = int(callback.data.split('_')[-1])
	except (ValueError, IndexError):
		await callback.answer("❌ Некорректный идентификатор", show_alert=True)
		return

	dialog_text = await _format_history(services, user_id)
	await services.chat.mark_read(user_id)
	await state.update_data(chat_user_id=user_id)
	await state.set_state(ChatStates.LIST)
	await callback.message.edit_text(
		dialog_text,
		reply_markup=AdminKeyboards.chat_dialog_controls(user_id)
	)
	await callback.answer()


@router.callback_query(F.data.startswith("admin_messages_reply_"))
async def start_reply(callback: types.CallbackQuery, state: FSMContext, services: Services):
	try:
		user_id = int(callback.data.split('_')[-1])
	except (ValueError, IndexError):
		await callback.answer("❌ Некорректный идентификатор", show_alert=True)
		return

	user = await services.user.get_user_by_id(user_id)
	if not user:
		await callback.answer("❌ Пользователь не найден", show_alert=True)
		return

	await state.set_state(ChatStates.WAITING_REPLY)
	await state.update_data(chat_user_id=user_id)
	await callback.message.answer(
		"✏️ <b>Введите сообщение для пользователя</b>\n\n"
		f"Получатель: {html.escape(user.full_name)} (ID: <code>{user.user_id}</code>)",
		reply_markup=AdminKeyboards.chat_reply_cancel(user_id)
	)
	await callback.answer()


@router.message(ChatStates.WAITING_REPLY)
async def send_reply(message: types.Message, state: FSMContext, services: Services, admin: Admin | None = None):
	data = await state.get_data()
	user_id = data.get('chat_user_id')
	if not user_id:
		await message.answer("❌ Диалог не выбран")
		await state.clear()
		return

	text = (message.text or '').strip()
	if not text:
		await message.answer("❌ Сообщение не может быть пустым")
		return

	if not admin:
		admin = await services.admin.get_admin(message.from_user.id)

	if not admin:
		await message.answer("❌ Нет прав для отправки сообщений")
		await state.clear()
		return

	is_sent = await services.chat.send_reply(admin.user_id, user_id, text)

	if not is_sent:
		await message.answer("❌ Не удалось отправить сообщение")
		return

	await message.answer("✅ Сообщение отправлено пользователю")

	dialog_text = await _format_history(services, user_id)
	await message.answer(
		dialog_text,
		reply_markup=AdminKeyboards.chat_dialog_controls(user_id)
	)
	await state.set_state(ChatStates.LIST)