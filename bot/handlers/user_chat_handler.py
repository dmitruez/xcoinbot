from aiogram import F, Router, types
from aiogram.filters import StateFilter

from ..services import Services


router = Router(name=__name__)


@router.message(StateFilter(None), F.text, F.text != "/admin")
async def forward_user_message(message: types.Message, services: Services):
	if message.text.startswith('/'):
		return

	admin = await services.admin.get_admin(message.from_user.id)
	if admin:
		return

	user = await services.user.get_user_by_id(message.from_user.id)
	if not user or not user.captcha_passed:
		return

	text = message.text.strip()
	if not text:
		await message.answer("❌ Сообщение не может быть пустым")
		return

	saved = await services.chat.save_user_message(user.user_id, text)
	if not saved:
		await message.answer("❌ Не удалось отправить сообщение, попробуйте позже")
		return

	await services.chat.notify_admins_about_user_message(user, text)
	await message.answer("✅ Сообщение отправлено администрации")
