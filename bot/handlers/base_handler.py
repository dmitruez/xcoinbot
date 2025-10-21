from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from ..handlers.captcha_handler import send_captcha
from ..keyboards.user_keyboard import UserKeyboards
from ..models import User
from ..services import Services


router = Router(name=__name__)


@router.message(CommandStart())
async def start_command(message: types.Message, services: Services, state: FSMContext):
	"""Обработка команды /start с капчей"""
	user_id = message.from_user.id

	# Проверяем существование пользователя
	user = await services.user.get_user_by_id(user_id)
	if not user:
		# Создаем нового пользователя
		user = User(
			user_id=user_id,
			username=message.from_user.username,
			full_name=message.from_user.full_name,
			captcha_passed=False
		)
		await services.user.create_user(user)

	# Если капча уже пройдена
	if user.captcha_passed:
		# # Получаем основной канал
		channel = await services.channel.get_main_channel()
		text, media_type, media_id, buttons = await services.welcome.format_message(channel)
		keyboard = await services.welcome.format_keyboard(buttons)
		if channel:
			await services.welcome.send_message(user_id, text, media_type, media_id, keyboard)
		else:
			await message.answer(text, reply_markup=keyboard)
		await message.answer("📋 Главное меню", reply_markup=UserKeyboards.main_menu())
		return

	await send_captcha(message, state, services)



@router.callback_query(F.data == 'delete_this_message')
async def delete_this_message(callback: types.CallbackQuery):
	await callback.message.delete()

