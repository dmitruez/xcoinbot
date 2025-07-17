# Third party
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from aiogram.exceptions import TelegramNotFound
from xcoinbot.bot.services import Services
from xcoinbot.bot.config import Config



async def setup_commands(bot: Bot, services: Services):
    base_commands = [
        BotCommand(command='/start', description="🚀 Запуск бота 🚀"),
        BotCommand(command='/channel', description="Ссылка на актуальный канал")
    ]

    regular_admin_commands = [
        BotCommand(command='/stats', description="Статистика пользователей"),
        BotCommand(command='/admin', description="Админ панель")
    ]

    super_admin_commands = [
        BotCommand(command='/ban', description="Забанить пользователя по ID"),
        BotCommand(command='/unban', description="Разблокировать пользователя по ID"),
        BotCommand(command='/set_backup_channel', description="Сменить резервный канал"),
        BotCommand(command='/edit_notification', description="Измненение сообщения рассылки")
    ]

    developer_commands = [
        BotCommand(command='/logs', description='Получить Логи'),
        BotCommand(command='/backup', description="Сделать бэкап"),
    ]

    await bot.set_my_commands(base_commands, scope=BotCommandScopeDefault())

    regular_admins, super_admins = await services.admin.list_admins()

    for regular_admin in regular_admins:
        try:
            await bot.set_my_commands(regular_admin_commands,
                                      scope=BotCommandScopeChat(chat_id=regular_admin.user_id))
        except TelegramNotFound:
            pass

    for super_admin in super_admins:
        try:
            await bot.set_my_commands(regular_admin_commands + super_admin_commands,
                                      scope=BotCommandScopeChat(chat_id=super_admin.user_id)
                                      )
        except TelegramNotFound:
            pass

    for developer_id in Config.DEVELOPERS_IDS:
        try:
            await bot.set_my_commands(regular_admin_commands + super_admin_commands + developer_commands,
                                      scope=BotCommandScopeChat(chat_id=developer_id)
                                      )
        except TelegramNotFound:
            pass

async def delete_commands(bot: Bot, services: Services):
    await bot.set_my_commands([], scope=BotCommandScopeDefault())
    regular_admins, super_admins = await services.admin.list_admins()

    for admin in regular_admins + super_admins:
        await bot.set_my_commands([], scope=BotCommandScopeChat(chat_id=admin.user_id))
