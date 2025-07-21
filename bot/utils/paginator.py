from dataclasses import dataclass
from typing import List, TypeVar, Generic, Tuple


T = TypeVar('T')


@dataclass
class Page(Generic[T]):
	items: List[T]
	page: int
	total_pages: int
	total_items: int


class Paginator(Generic[T]):
	"""Улучшенный пагинатор с дополнительной информацией"""

	def __init__(self, items: List[T], per_page: int = 8):
		self.items = items
		self.per_page = per_page
		self.total_items = len(items)
		self.total_pages = max(1, (self.total_items + per_page - 1) // per_page)

	def get_page(self, page: int) -> Page[T]:
		"""Получает страницу с метаданными"""
		if page < 1 or page > self.total_pages:
			raise ValueError("Invalid page number")

		start = (page - 1) * self.per_page
		end = start + self.per_page
		return Page(
			items=self.items[start:end],
			page=page,
			total_pages=self.total_pages,
			total_items=self.total_items
		)

	def get_pagination_buttons(self, current_page: int, prefix: str) -> List[Tuple[str, str]]:
		"""Генерирует кнопки пагинации"""
		buttons = []
		if current_page > 1:
			buttons.append(("⬅️ Назад", f"{prefix}_page_{current_page - 1}"))

		if current_page < self.total_pages:
			buttons.append(("Вперед ➡️", f"{prefix}_page_{current_page + 1}"))

		return buttons
