from aiogram import Dispatcher

from .admin_middleware import AdminMiddleware, AdminCallbackMiddleware
from .data_handler_middleware import DataHandlerMiddleware
from .subscription_middleware import SubscriptionMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
	"""Инициализация всех мидлварей"""
	dp.message.middleware(AdminMiddleware(services=dp["services"]))
	dp.update.outer_middleware.register(DataHandlerMiddleware(repos=dp["repos"], services=dp["services"]))
	dp.message.middleware(SubscriptionMiddleware(services=dp["services"]))
	dp.callback_query.middleware.register(AdminCallbackMiddleware(services=dp["services"]))