# Проверка капчи
from datetime import datetime, timedelta

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, InputMediaPhoto

from ..keyboards.user_keyboard import UserKeyboards
from ..services import Services
from ..states.base_states import CaptchaStates
from ..utils.work_with_date import get_datetime_now


router = Router(name=__name__)


async def send_captcha(message: Message, state: FSMContext, services: Services):
	state_data = await state.get_data()
	now = get_datetime_now()
	attemps = state_data.get("attemps", 0)
	refreshes = state_data.get("refreshes", 0)

	if ban := state_data.get("ban"):
		if now < ban:
			time = ban - now
			minutes, seconds = divmod(time.seconds, 60)
			await message.answer(
				"❌ У вас закончились обновления каптчи ❌\n\n"
				f"До разбана: {minutes}:{seconds}"
			)
			return
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
	await state.update_data(captcha_message=captcha_message, attemps=attemps, refreshes=refreshes)
	await state.set_state(CaptchaStates.WAITING_CAPTCHA)



@router.message(F.text, CaptchaStates.WAITING_CAPTCHA)
async def check_captcha(message: types.Message, services: Services, state: FSMContext):
	"""Проверка введенной капчи"""
	await message.delete()
	# if len(message.text) > 6:
	# 	return
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

		# Проверяем подписку на резервный канал
		is_subscribed = await services.channel.check_subscription(message.from_user.id)
		if is_subscribed:
			# # Получаем основной канал
			channel = await services.channel.get_main_channel()
			await captcha_message.delete()
			if channel:
				await services.welcome.send_welcome(user_id, channel)

			else:
				await message.answer("✅ Капча успешно пройдена! Добро пожаловать!")
			await message.answer("📋 Главное меню", reply_markup=UserKeyboards.main_menu())
		else:
			# Если не подписан - просим подписаться
			backup_channel = await services.channel.get_backup_channel()
			if backup_channel:
				await message.answer(
					"⚠ Для использования бота необходимо подписаться на резервный канал:\n"
					f"@{backup_channel.username}" if backup_channel.username else
					f"Ссылка: {backup_channel.link}"
				)
			else:
				await message.answer("⚠ Резервный канал не настроен. Обратитесь к администратору.")
	else:
		# Если остались попытки, показываем новую капчу
		if attemps < 3:
			captcha_text, image_path = await services.captcha.generate_captcha(user_id, attemps=attemps)
			captcha_message = await captcha_message.edit_media(
				media=InputMediaPhoto(media=FSInputFile(image_path), caption=f"{response}\n\n🔐 Пожалуйста, попробуйте еще раз. Введите текст с изображения:"),
				reply_markup=UserKeyboards.captcha_refresh()
			)
			# Удаляем файл после отправки
			await services.captcha.cleanup(image_path)
			await state.update_data(attemps=attemps, captcha_message=captcha_message)
		else:
			await services.user.ban_user(user_id)
			await captcha_message.delete()
			await message.answer(response)


@router.callback_query(F.data == "refresh_captcha")
async def refresh_captcha_handler(callback: types.CallbackQuery, services: Services, state: FSMContext):
	"""Обновление капчи по запросу пользователя"""
	user_id = callback.from_user.id
	state_data = await state.get_data()
	refreshes = state_data.get("refreshes", 0) + 1

	markup = UserKeyboards.captcha_refresh()
	caption = f"🔄 Капча обновлена. Доступных обновлений: {5 - refreshes}.\n\nВведите текст с изображения:"

	if refreshes > 4:
		markup = None
		caption = "🔄 Капча обновлена. Больше не осталось обновлений.\n\nВведите текст с изображения:"
		await state.update_data(ban=get_datetime_now() + timedelta(minutes=1))

	# Генерируем новую капчу
	captcha_text, image_path = await services.captcha.generate_captcha(user_id, attemps=state_data['attemps'])

	# Отправляем новую капчу
	await callback.message.edit_media(
		media=InputMediaPhoto(media=FSInputFile(image_path), caption=caption),
		reply_markup=markup
	)
	# Удаляем файл после отправки
	await services.captcha.cleanup(image_path)
	await state.update_data(refreshes=refreshes)
	await callback.answer()
