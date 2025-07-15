import asyncpg
from ..models import User, Channel, Admin, Captcha
from .user_repository import UserRepository
from .channel_repository import ChannelRepository
from .admin_repository import AdminRepository
from .captcha_repository import CaptchaRepository


class Repositories:
	"""Контейнер для всех репозиториев"""

	def __init__(self, pool: asyncpg.Pool):
		self.user = UserRepository(pool)
		self.channel = ChannelRepository(pool)
		self.admin = AdminRepository(pool)
		self.captcha = CaptchaRepository(pool)

	async def create_tables(self) -> None:
		"""Создание всех таблиц в БД"""
		await self.user.create_table()
		await self.channel.create_table()
		await self.admin.create_table()
		await self.captcha.create_table()


async def setup_repositories(pool: asyncpg.Pool) -> Repositories:
	"""Инициализация всех репозиториев"""
	repos = Repositories(pool)
	await repos.create_tables()
	return repos