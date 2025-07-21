from aiogram import Bot

from .admin_service import AdminService
from .captcha_service import CaptchaService
from .channel_service import ChannelService
from .notifier_service import NotificationService
from .subscriber_service import SubscriptionService
from .user_service import UserService
from ..repositories import Repositories


class Services:
	"""Контейнер для всех сервисов"""

	def __init__(self, bot: Bot, repos: Repositories):
		self.captcha: CaptchaService = CaptchaService(repos.captcha)
		self.channel: ChannelService = ChannelService(bot, repos.channel)
		self.notification: NotificationService = NotificationService(bot, repos)
		self.subscriber: SubscriptionService = SubscriptionService(bot, repos.user, repos.channel)
		self.user: UserService = UserService(repos.user)
		self.admin: AdminService = AdminService(repos.admin, repos.user, repos.channel)


def setup_services(bot: Bot, repos: Repositories) -> Services:
	"""Инициализация всех сервисов"""
	return Services(bot, repos)
