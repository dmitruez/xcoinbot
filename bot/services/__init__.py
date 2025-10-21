from aiogram import Bot

from .admin_service import AdminService
from .broadcast_service import BroadcastService
from .captcha_service import CaptchaService
from .channel_service import ChannelService
from .message_service import MessageService
from .notifier_service import NotificationService
from .subscriber_service import SubscriptionService
from .user_service import UserService
from .welcome_service import WelcomeService
from ..repositories import Repositories
from .chat_service import ChatService


class Services:
	"""Контейнер для всех сервисов"""

	def __init__(self, bot: Bot, repos: Repositories):
		self.captcha: CaptchaService = CaptchaService(repos.captcha)
		self.channel: ChannelService = ChannelService(bot, repos.channel)
		self.notification: NotificationService = NotificationService(bot, repos)
		self.subscriber: SubscriptionService = SubscriptionService(bot, repos.user, repos.channel)
		self.user: UserService = UserService(repos.user, admin_repo=repos.admin)
		self.admin: AdminService = AdminService(repos.admin, repos.user, repos.channel)
		self.welcome: WelcomeService = WelcomeService(bot, repos)
		self.broadcast: BroadcastService = BroadcastService(repos.broadcast, repos.admin)
		self.chat: ChatService = ChatService(bot, repos.chat, repos.admin, repos.user)


def setup_services(bot: Bot, repos: Repositories) -> Services:
	"""Инициализация всех сервисов"""
	return Services(bot, repos)
