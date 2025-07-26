from aiogram import Dispatcher

from .admin_middleware import AdminMiddleware, AdminCallbackMiddleware
from .data_handler_middleware import DataHandlerMiddleware
from .logger_handler import LoggerMiddleware
from .subscription_middleware import SubscriptionMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
	"""Инициализация всех мидлварей"""
	dp.message.middleware.register(AdminMiddleware(services=dp["services"]))
	dp.message.middleware.register(SubscriptionMiddleware(services=dp["services"]))
	dp.callback_query.middleware.register(AdminCallbackMiddleware(services=dp["services"]))
	dp.update.outer_middleware.register(LoggerMiddleware())
	dp.update.outer_middleware.register(DataHandlerMiddleware(repos=dp["repos"], services=dp["services"]))