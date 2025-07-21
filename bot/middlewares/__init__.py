from aiogram import Dispatcher

from .admin_middleware import AdminMiddleware
from .data_handler_middleware import DataHandlerMiddleware


def setup_middlewares(dp: Dispatcher) -> None:
	"""Инициализация всех мидлварей"""
	dp.message.middleware(AdminMiddleware(services=dp["services"]))
	dp.update.outer_middleware.register(DataHandlerMiddleware(repos=dp["repos"], services=dp["services"]))
