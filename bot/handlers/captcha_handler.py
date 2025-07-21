# Проверка капчи
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InputMediaPhoto

from ..keyboards.user_keyboard import UserKeyboards
from ..services import Services
from ..states.base_states import CaptchaStates


router = Router(name=__name__)


async def send_captcha(message: Message, state: FSMContext, services: Services):
	user_id = message.from_user.id
	# Генерируем и отправляем капчу
	captcha_text, image_path = await services.captcha.generate_captcha(user_id)


	# Отправляем капчу как файл
	captcha_message = await message.answer_photo(
		photo=FSInputFile(image_path),
		caption="🔐 Для доступа к боту решите капчу. Введите текст с изображения:",
		reply_markup=UserKeyboards.captcha_refresh()
	)
	# Удаляем файл после отправки
	await services.captcha.cleanup(image_path)
	await state.update_data(captcha_message=captcha_message, attemps=0)
	await state.set_state(CaptchaStates.WAITING_CAPTCHA)



@router.message(F.text, CaptchaStates.WAITING_CAPTCHA)
async def check_captcha(message: types.Message, services: Services, state: FSMContext):
	"""Проверка введенной капчи"""
	await message.delete()
	if len(message.text) > 6:
		return
	user_id = message.from_user.id
	user_input = message.text.strip()

	# Проверяем капчу
	success, response, attemps = await services.captcha.verify_captcha(user_id, user_input)

	# Очищаем временный файл капчи
	state_data = await state.get_data()
	captcha_message: Message = state_data["captcha_message"]

	if success:
		# Обновляем статус пользователя
		await services.user.mark_captcha_passed(user_id)
		await state.clear()

		# Получаем основной канал
		channel = await services.channel.get_main_channel()
		if channel:
			await message.answer(
				f"✅ Капча успешно пройдена!\n"
				f"Добро пожаловать! Основной канал: {channel.link}"
			)
		else:
			await message.answer("✅ Капча успешно пройдена! Добро пожаловать!")
	else:
		# await message.answer(response)
		pass

		# Если остались попытки, показываем новую капчу
		if attemps < 3:
			captcha_text, image_path = await services.captcha.generate_captcha(user_id, attemps=attemps)
			captcha_message = await captcha_message.edit_media(
				media=InputMediaPhoto(media=FSInputFile(image_path)),
				reply_markup=UserKeyboards.captcha_refresh()
			)
			await captcha_message.edit_caption(
				caption=f"{response}\n\n🔐 Пожалуйста, попробуйте еще раз. Введите текст с изображения:",
				reply_markup=UserKeyboards.captcha_refresh()
			)
			# Удаляем файл после отправки
			await services.captcha.cleanup(image_path)
			await state.update_data(attemps=attemps, captcha_message=captcha_message)
		else:
			await services.user.ban_user(user_id)


@router.callback_query(F.data == "refresh_captcha")
async def refresh_captcha_handler(callback: types.CallbackQuery, services: Services, state: FSMContext):
	"""Обновление капчи по запросу пользователя"""
	user_id = callback.from_user.id
	state_data = await state.get_data()

	# Генерируем новую капчу
	captcha_text, image_path = await services.captcha.generate_captcha(user_id, attemps=state_data['attemps'])

	# Отправляем новую капчу
	await callback.message.edit_media(
		media=InputMediaPhoto(media=FSInputFile(image_path)),
		reply_markup=UserKeyboards.captcha_refresh()
	)
	await callback.message.edit_caption(
		caption="🔄 Капча обновлена. Введите текст с изображения:",
		reply_markup=UserKeyboards.captcha_refresh()
	)
	# Удаляем файл после отправки
	await services.captcha.cleanup(image_path)
	await callback.answer()