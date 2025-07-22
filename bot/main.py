from functools import partial

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNotFound, TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage

from .config import Config
from .handlers import register_handlers
from .middlewares import setup_middlewares
from .repositories import setup_repositories
from .services import setup_services, Services
from .utils.commands import setup_commands, delete_commands
from .utils.loggers import main_bot as logger


async def start_bot(bot: Bot, dp: Dispatcher):
	try:
		# Создаём зависимости
		pool = await create_pool()
		repos = await setup_repositories(pool)
		services = setup_services(bot, repos)

		# Сохраняем в bot.data для глобального доступа
		dp['repos'] = repos
		dp['services'] = services

		# Ставим команды
		await setup_commands(bot, services)

		# # Настройка middleware
		setup_middlewares(dp)

		# Регистрация обработчиков
		register_handlers(dp)

		_, super_admins = await services.admin.list_admins()

		for admin in super_admins:
			try:
				await bot.send_message(admin.user_id, text="🚀 Бот Запущен 🚀")
			except (TelegramNotFound, TelegramBadRequest):
				pass

	# for developer_id in Config.DEVELOPERS_IDS:
	# 	try:
	# 		await bot.send_message(developer_id, text="🚀 Бот Запущен 🚀")
	# 	except TelegramNotFound:
	# 		pass

	except Exception as e:
		logger.exception(e)


async def shutdown_bot(bot: Bot, dp: Dispatcher):
	services: Services = dp["services"]

	_, super_admins = await services.admin.list_admins()

	for admin in super_admins:
		try:
			await bot.send_message(admin.user_id, text="🛑 Бот Остановлен 🛑")
		except TelegramNotFound:
			pass

	# for developer_id in Config.DEVELOPERS_IDS:
	# 	try:
	# 		await bot.send_message(developer_id, text="🛑 Бот Остановлен 🛑")
	# 	except TelegramNotFound:
	# 		pass

	await delete_commands(bot, services)


async def create_pool():
	return await asyncpg.create_pool(
		dsn=f"postgresql://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}",
		# или полный URL
		min_size=5,  # Минимальное число подключений
		max_size=20,  # Максимальное число подключений
		timeout=30,  # Таймаут подключения (секунды)
		command_timeout=60,  # Таймаут выполнения запроса
		max_inactive_connection_lifetime=300,  # Закрывать неиспользуемые подключения
	)


async def main():
	# Инициализация
	bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
	dp = Dispatcher(storage=MemoryStorage())

	# Создаем функции запуска и окончания сеанса с параметрами
	start = partial(start_bot, bot, dp)
	end = partial(shutdown_bot, bot, dp)

	# Регистрируем их
	dp.startup.register(start)
	dp.shutdown.register(end)

	try:
		logger.info("Bot started")
		await dp.start_polling(bot)
	finally:
		await bot.session.close()
