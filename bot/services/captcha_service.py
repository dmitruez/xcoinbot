import os
import random
from string import ascii_letters, digits
from tempfile import NamedTemporaryFile
from typing import Tuple

from PIL import ImageFont
from captcha.image import ImageCaptcha

from ..models import Captcha
from ..repositories import CaptchaRepository
from ..utils.loggers import services as logger


class TextCaptcha:
	"""Генератор текстовой капчи"""

	def __init__(self):
		# Исключаем похожие символы
		self._excluded_chars = 'lI1oO0'
		self._chars = [c for c in ascii_letters + digits if c not in self._excluded_chars]
		self._length = 5
		self._width = 240
		self._height = 120
		self._font_path = self._get_font_path()
		self._temp_dir = "temp_captchas"
		os.makedirs(self._temp_dir, exist_ok=True)

	def _get_font_path(self) -> str:
		"""Поиск доступного шрифта"""
		font_paths = [
			"assets/fonts/arial.ttf",
			"assets/fonts/Roboto-Regular.ttf",
			"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Для Linux
		]

		for path in font_paths:
			if os.path.exists(path):
				return path

		# Используем дефолтный шрифт
		return ImageFont.load_default().path

	async def generate(self) -> Tuple[str, str]:
		"""Генерация капчи и возврат (текст, файл)"""
		# Генерируем текст
		text = ''.join(random.choice(self._chars) for _ in range(self._length))

		# Создаем временный файл
		temp_file = NamedTemporaryFile(
			dir=self._temp_dir,
			suffix=".png",
			delete=False
		)
		file_path = temp_file.name
		temp_file.close()

		# Генерируем изображение
		image = ImageCaptcha(width=self._width, height=self._height)
		image.write(text, file_path)

		return text, file_path

	async def cleanup(self, file_path: str):
		"""Удаление временного файла"""
		if file_path and os.path.exists(file_path):
			try:
				os.unlink(file_path)
			except Exception as e:
				logger.exception(f"Error while deleting file: {file_path}")


class CaptchaService:
	"""Сервис для работы с капчей"""

	def __init__(self, captcha_repo: CaptchaRepository):
		self.captcha_repo = captcha_repo
		self.text_captcha = TextCaptcha()

	async def generate_captcha(self, user_id: int, attemps=0) -> Tuple[str, str]:
		"""Генерация капчи"""
		answer, image = await self.text_captcha.generate()

		# Сохраняем в базу
		captcha = Captcha(
			user_id=user_id,
			text=str(answer),
			attempts=attemps
		)
		await self.captcha_repo.create(captcha)

		return str(answer), image

	async def verify_captcha(self, user_id: int, user_input: str) -> Tuple[bool, str, int]:
		"""Проверка капчи"""
		captcha = await self.captcha_repo.get(user_id)
		if not captcha:
			return False, "Капча не найдена. Пожалуйста, запросите новую.", 0

		# Увеличиваем счетчик попыток
		await self.captcha_repo.increment_attempts(user_id)

		if user_input.strip() != captcha.text:
			attempts = await self.captcha_repo.get_attempts(user_id)
			remaining = 3 - attempts

			if remaining <= 0:
				await self.captcha_repo.delete(user_id)
				return False, "❌ Превышено количество попыток. Вы заблокированы.", 3

			return False, f"❌ Неверно! Осталось попыток: {remaining}", attempts

		# Капча пройдена
		await self.captcha_repo.delete(user_id)
		return True, "✅ Капча успешно пройдена!", 0

	async def cleanup(self, file_path: str):
		"""Очистка временных файлов"""
		await self.text_captcha.cleanup(file_path)
