from typing import List, TypeVar


T = TypeVar('T')


class Paginator:
	"""Утилита для пагинации списков"""

	def __init__(self, items: List[T], per_page: int = 10):
		self.items = items
		self.per_page = per_page
		self.total_pages = (len(items) + per_page - 1) // per_page

	def get_page(self, page: int) -> List[T]:
		"""Получение страницы с элементами"""
		start = (page - 1) * self.per_page
		end = start + self.per_page
		return self.items[start:end]

	def has_next(self, page: int) -> bool:
		"""Есть ли следующая страница"""
		return page < self.total_pages

	def has_previous(self, page: int) -> bool:
		"""Есть ли предыдущая страница"""
		return page > 1