from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile

from ...keyboards.admin_keyboard import AdminKeyboards
from ...models import Admin
from ...services import Services


router = Router(name=__name__)


@router.message(Command('channel'))
async def get_main_channel(message: types.Message, services: Services):
	channel = await services.channel.get_main_channel()
	await message.answer(
		f"Актуальная ссылка на канал: 👇\n"
		f"<b><a href='{channel.link}'>{channel.title}</a></b>"
	)


@router.message(Command("admin"))
async def admin_panel(message: types.Message, admin: Admin):
	"""Главное меню админ-панели"""
	await message.answer(
		"👑 Добро пожаловать в админ-панель!",
		reply_markup=AdminKeyboards.main_menu(admin.level)
	)

@router.callback_query(F.data == "admin_main")
async def admin_main(callback: types.CallbackQuery, services: Services):
	"""Обработка возврата в главное меню"""
	admin = await services.admin.get_admin(callback.from_user.id)

	await callback.message.edit_text(
		"👑 Добро пожаловать в админ-панель!",
		reply_markup=AdminKeyboards.main_menu(admin.level)
	)
	await callback.answer()


@router.message(Command('logs'))
async def logs(message: types, services: Services):
	await get_logs(message, services)



@router.callback_query(F.data == "admin_logs")
async def get_logs(callback: types.CallbackQuery | types.Message, services: Services):
	"""Получение логов"""
	log_files = await services.admin.get_logs()

	if log_files:
		if isinstance(callback, types.CallbackQuery):
			await callback.message.edit_text(
				text="📜 Выберите нужные логи бота",
				reply_markup=AdminKeyboards.logs_buttons(log_files)
			)
			await callback.answer()
		else:
			await callback.answer(
				text="📜 Выберите нужные логи бота",
				reply_markup=AdminKeyboards.logs_buttons(log_files)
			)
	else:
		await callback.answer("❌ Файл логов не найден", show_alert=True)




@router.callback_query(F.data.startswith("logs-"))
async def send_log(callback: types.CallbackQuery):
	log_file = callback.data.split('-')[1]
	await callback.bot.send_document(
		chat_id=callback.from_user.id,
		document=FSInputFile('logs/' + log_file + '.log'),
		caption=f"✔ Файл логов за <b>{log_file}</b>"
	)
	await callback.answer()


@router.callback_query(F.data == "admin_backup")
async def create_backup(callback: types.CallbackQuery, services: Services):
	"""Создание бэкапа"""
	await callback.answer("⏳ Создание бэкапа...")

	# backup_file = await services.admin.create_backup()
	# if backup_file:
	# 	await callback.bot.send_document(
	# 		chat_id=callback.from_user.id,
	# 		document=backup_file,
	# 		caption="💾 Бэкап базы данных"
	# 	)
	# else:
	# 	await callback.answer("❌ Ошибка создания бэкапа", show_alert=True)
	#
	# await callback.answer()
