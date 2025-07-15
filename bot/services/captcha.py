# Кастомная капча

import io
import random
import string
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont

from ..models import Captcha
from ..repositories.captcha_repository import CaptchaRepository


class CaptchaService:
	"""Сервис для генерации и проверки капчи"""

	def __init__(self, captcha_repo: CaptchaRepository):
		self.captcha_repo = captcha_repo
		self.font_path = "assets/fonts/arial.ttf"  # Путь к шрифту

	async def _generate_captcha_image(self, text: str) -> io.BytesIO:
		"""Генерация изображения капчи"""
		try:
			# Параметры изображения
			width, height = 200, 80
			background_color = (255, 255, 255)  # Белый фон

			# Создаем изображение
			image = Image.new('RGB', (width, height), color=background_color)
			draw = ImageDraw.Draw(image)

			# Загружаем шрифт
			try:
				font = ImageFont.truetype(self.font_path, size=36)
			except:
				font = ImageFont.load_default()

			# Рисуем каждый символ с искажениями
			char_width = 30
			start_x = 10

			for i, char in enumerate(text):
				# Параметры искажения для символа
				x = start_x + i * char_width + random.randint(-5, 5)
				y = 20 + random.randint(-10, 10)
				angle = random.randint(-25, 25)
				color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))  # Темные цвета

				# Создаем временное изображение для символа
				char_image = Image.new('RGBA', (char_width, 50), (255, 255, 255, 0))
				char_draw = ImageDraw.Draw(char_image)
				char_draw.text((0, 0), char, font=font, fill=color)

				# Поворачиваем символ
				char_image = char_image.rotate(angle, expand=1)

				# Накладываем символ на основное изображение
				image.paste(char_image, (x, y), char_image)

			# Добавляем линии-помехи
			for _ in range(5):
				x1 = random.randint(0, width)
				y1 = random.randint(0, height)
				x2 = random.randint(0, width)
				y2 = random.randint(0, height)
				line_color = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200))
				draw.line([(x1, y1), (x2, y2)], fill=line_color, width=1)

			# Добавляем случайные точки
			for _ in range(100):
				x = random.randint(0, width - 1)
				y = random.randint(0, height - 1)
				point_color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
				draw.point((x, y), fill=point_color)

			# Сохраняем в буфер
			buffer = io.BytesIO()
			image.save(buffer, format='PNG')
			buffer.seek(0)

			return buffer
		except Exception as e:
			raise


	@staticmethod
	def _add_noise(image: Image.Image) -> None:
		"""Добавление шума на изображение капчи"""
		width, height = image.size
		pixels = image.load()

		# Добавляем случайные точки
		for _ in range(int(width * height * 0.1)):
			x, y = random.randint(0, width - 1), random.randint(0, height - 1)
			pixels[x, y] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

		# Добавляем случайные линии
		draw = ImageDraw.Draw(image)
		for _ in range(5):
			x1, y1 = random.randint(0, width), random.randint(0, height)
			x2, y2 = random.randint(0, width), random.randint(0, height)
			draw.line([(x1, y1), (x2, y2)],
					  fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), width=1)

	async def generate_captcha(self, user_id: int) -> Tuple[str, io.BytesIO]:
		"""
		Генерация новой капчи для пользователя
		:param user_id: ID пользователя
		:return: Кортеж (текст капчи, изображение в BytesIO)
		"""
		# Генерируем текст капчи (исключаем похожие символы)
		chars = string.ascii_letters + string.digits
		ambiguous = 'lI1oO0'
		chars = ''.join(c for c in chars if c not in ambiguous)
		captcha_text = ''.join(random.choice(chars) for _ in range(6))

		# Генерируем изображение
		image_buffer = await self._generate_captcha_image(captcha_text)

		# Сохраняем в базу данных
		captcha = Captcha(
			user_id=user_id,
			text=captcha_text,
			attempts=0
		)
		await self.captcha_repo.create(captcha)

		return captcha_text, image_buffer

	async def verify_captcha(self, user_id: int, user_input: str) -> Tuple[bool, str]:
		"""
		Проверка капчи пользователя
		:param user_id: ID пользователя
		:param user_input: Введенный пользователем текст
		:return: Кортеж (результат проверки, сообщение)
		"""
		captcha = await self.captcha_repo.get(user_id)
		if not captcha:
			return False, "Капча не найдена. Пожалуйста, запросите новую."

		# Увеличиваем счетчик попыток
		await self.captcha_repo.increment_attempts(user_id)

		if user_input.lower() != captcha.text.lower():
			attempts = await self.captcha_repo.get_attempts(user_id)
			remaining_attempts = 3 - attempts

			if remaining_attempts <= 0:
				await self.captcha_repo.delete(user_id)
				return False, "❌ Превышено количество попыток. Вы заблокированы."

			return False, f"❌ Неверно! Осталось попыток: {remaining_attempts}"

		# Капча пройдена
		await self.captcha_repo.delete(user_id)
		return True, "✅ Капча успешно пройдена!"