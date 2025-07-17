from aiogram import Bot
from ..repositories import Repositories
from .captcha import CaptchaService
from .channel import ChannelService
from .notifier import NotificationService
from .subscriber import SubscriptionService
from .user import UserService
from .admin import AdminService


class Services:
	"""Контейнер для всех сервисов"""

	def __init__(self, bot: Bot, repos: Repositories):
		self.captcha: CaptchaService = CaptchaService(repos.captcha)
		self.channel: ChannelService = ChannelService(bot, repos.channel)
		self.notification: NotificationService = NotificationService(bot, repos)
		self.subscriber: SubscriptionService = SubscriptionService(bot, repos.user, repos.channel)
		self.user: UserService = UserService(repos.user)
		self.admin: AdminService = AdminService(repos.admin)


def setup_services(bot: Bot, repos: Repositories) -> Services:
	"""Инициализация всех сервисов"""
	return Services(bot, repos)