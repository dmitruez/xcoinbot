from typing import List, Tuple

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..models import User


class AdminKeyboards:
	@staticmethod
	def main_menu(admin_level: int):
		"""Главное меню админ-панели в зависимости от уровня"""
		builder = InlineKeyboardBuilder()
		adjust = []

		# Кнопки для всех админов
		builder.add(
			InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
			InlineKeyboardButton(text="👤 Пользователи", callback_data="admin_users"),
			InlineKeyboardButton(text="📝 Редактировать уведомление", callback_data="admin_notification"),
			InlineKeyboardButton(text="📝 Редактирование приветственного сообщения", callback_data="admin_welcome")
		)
		adjust.extend([2, 1])

		# Кнопки для super admin (уровень 2+)
		if admin_level >= 2:
			builder.add(
				InlineKeyboardButton(text="📢 Управление каналами", callback_data="admin_channels")
			)
			adjust.append(1)

		# Кнопки для developer (уровень 3)
		if admin_level >= 3:
			builder.add(
				InlineKeyboardButton(text="📜 Логи", callback_data="admin_logs"),
				InlineKeyboardButton(text="💾 Бэкап", callback_data="admin_backup")
			)
			adjust.append(2)

		builder.adjust(*adjust)
		return builder.as_markup()

	@staticmethod
	def users_menu():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_search_user"),
			InlineKeyboardButton(text="🧾 Список пользователей", callback_data="admin_users_list"), # НЕ РЕАЛИЗОВАНО
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_main")
		)
		builder.adjust(1)
		return builder.as_markup()

	@staticmethod
	def search_menu():
		"""Меню поиска пользователей"""
		builder = InlineKeyboardBuilder()
		builder.row(
			InlineKeyboardButton(text="🔍 По username", callback_data="admin_search_username"),
			width=1
		)
		builder.row(
			InlineKeyboardButton(text="🔍 По имени/фамилии", callback_data="admin_search_nickname"),
			width=1
		)
		builder.row(
			InlineKeyboardButton(text="🔍 По ID", callback_data="admin_search_id"),
			width=1
		)
		builder.row(
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_users"),
			width=1
		)
		return builder.as_markup()
	
	
	@staticmethod
	def admin_welcome():
		kb_builder = InlineKeyboardBuilder()
		kb_builder.button(text="✏️ Текст", callback_data="welcome_edit_text")
		kb_builder.button(text="🖼 Медиа", callback_data="welcome_edit_media")
		kb_builder.button(text="🔘 Кнопки", callback_data="welcome_manage_buttons")
		kb_builder.button(text="👀 Предпросмотр", callback_data="welcome_preview")
		kb_builder.button(text="◀️ Назад", callback_data="admin_menu")
		kb_builder.adjust(2, 2, 1)
		return kb_builder.as_markup()

	@staticmethod
	def cancel_search():
		"""Клавиатура отмены поиска"""
		builder = InlineKeyboardBuilder()
		builder.add(InlineKeyboardButton(
			text="❌ Отменить поиск",
			callback_data="admin_users"
		))
		return builder.as_markup()

	@staticmethod
	def back_to_search():
		"""Кнопка возврата к поиску"""
		builder = InlineKeyboardBuilder()
		builder.add(InlineKeyboardButton(
			text="🔙 Вернуться к поиску",
			callback_data="admin_search_menu"
		))
		return builder.as_markup()


	@staticmethod
	def profile_menu(user: User, is_admin: bool=False, admin_level: int=None, access_level: int = None) -> InlineKeyboardMarkup:
		builder = InlineKeyboardBuilder()
		adjust = []

		button_notif = InlineKeyboardButton(text="❌ Не уведомлять пользователя",
											callback_data=f"admin_ban_{user.user_id} ") \
			if user.should_notify else InlineKeyboardButton(text="✅ Уведомлять пользователя",
															callback_data=f"admin_unban_{user.user_id}")
		adjust.append(1)
		builder.add(
			button_notif
		)


		if access_level > 1:

			# Назначение/снятие админа
			if is_admin:
				builder.add(InlineKeyboardButton(
					text="👑 Снять админа",
					callback_data=f"admin_revoke_{user.user_id}"
				))
			else:
				builder.add(InlineKeyboardButton(
					text="👑 Назначить админом",
					callback_data=f"admin_grant_{user.user_id}"
				))

			adjust.append(1)

			# Управление уровнем админа
			if is_admin:
				builder.row(
					InlineKeyboardButton(text=f"Текущий уровень: {admin_level}", callback_data="no_action"),
					width=1
				)
				for level in [1, 2, 3]:
					if level != admin_level:
						builder.add(InlineKeyboardButton(
							text=f"Установить уровень {level}",
							callback_data=f"admin_setlevel_{user.user_id}_{level}"
						))
				adjust.extend([1, 2])

		builder.add(
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_users")
		)
		adjust.append(1)
		builder.adjust(*adjust)
		return builder.as_markup()

	@staticmethod
	def channels_menu():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="🔄 Сменить основной канал", callback_data="admin_change_main"),
			InlineKeyboardButton(text="🔄 Сменить резервный канал", callback_data="admin_change_backup"),
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_main")
		)
		builder.adjust(2)
		return builder.as_markup()

	@staticmethod
	def back_to_main():
		builder = InlineKeyboardBuilder()
		builder.add(InlineKeyboardButton(text="◀ В главное меню", callback_data="admin_main"))
		return builder.as_markup()

	@staticmethod
	def stats_menu():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="📅 За период", callback_data="admin_stats_period"),
			InlineKeyboardButton(text="📊 За 7 дней", callback_data="admin_stats_7days"),
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_main")
		)
		builder.adjust(2)
		return builder.as_markup()

	@staticmethod
	def back_to_notification():
		builder = InlineKeyboardBuilder()
		builder.add(InlineKeyboardButton(text="◀ Назад в меню рассылки", callback_data="admin_notification"))
		return builder.as_markup()

	@staticmethod
	def buttons_menu():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="➕ Добавить кнопку", callback_data="admin_add_button"),
			InlineKeyboardButton(text="➖ Удалить кнопку", callback_data="admin_remove_button"),
			InlineKeyboardButton(text="🗑 Очистить все", callback_data="admin_clear_buttons"),
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_notification")
		)
		builder.adjust(2, 1, 1)
		return builder.as_markup()

	@staticmethod
	def confirm_send_menu():
		builder = InlineKeyboardBuilder()
		builder.add(
			InlineKeyboardButton(text="✅ Да, отправить", callback_data="confirm_send"),
			InlineKeyboardButton(text="❌ Отменить", callback_data="admin_notification"),
		)
		builder.adjust(2)
		return builder.as_markup()

	@staticmethod
	def back_to_buttons():
		builder = InlineKeyboardBuilder()
		builder.add(InlineKeyboardButton(text="◀ К списку кнопок", callback_data="admin_manage_buttons"))
		return builder.as_markup()

	@staticmethod
	def remove_buttons(template):
		builder = InlineKeyboardBuilder()
		for i, btn in enumerate(template.buttons):
			builder.button(text=f"{i + 1}. {btn[0]}", callback_data=f"remove_button_{i}")

		builder.button(text="◀ Назад", callback_data="admin_manage_buttons")

		return builder.as_markup()

	@staticmethod
	def logs_buttons(log_files):
		builder = InlineKeyboardBuilder()

		for name in log_files[:7]:
			builder.button(text=name, callback_data=f'logs-{name}')

		builder.adjust(1)

		return builder.as_markup()

	@staticmethod
	def notification_menu():
		builder = InlineKeyboardBuilder()
		builder.row(
			InlineKeyboardButton(text="✏️ Редактировать текст", callback_data="admin_edit_text"),
			width=1
		)
		builder.row(
			InlineKeyboardButton(text="🔘 Управление кнопками", callback_data="admin_manage_buttons"),
			width=1
		)
		builder.row(
			InlineKeyboardButton(text="👀 Предпросмотр", callback_data="admin_preview_notification"),
			InlineKeyboardButton(text="✉️ Начать рассылку", callback_data="admin_send_notification"),
			width=2
		)
		builder.row(
			InlineKeyboardButton(text="◀ Назад", callback_data="admin_main"),
			width=1
		)
		return builder.as_markup()




	def channels_list(self, channels: List[Tuple[str, str]], current_page: int, total_pages: int, prefix: str):
		"""Клавиатура со списком каналов и пагинацией"""
		builder = InlineKeyboardBuilder()
		adjust = []
		# times, empty_button = divmod(len(channels), 2)
		for i in range(len(channels) - 1):
			adjust.append(1)
		# if empty_button:
		# 	adjust.append(2)

		# Кнопки каналов
		for text, callback_data in channels:
			builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))

		# if empty_button:
		# 	builder.add(InlineKeyboardButton(text="_", callback_data="_"))

		# Кнопки пагинации
		self._add_pagination_buttons(builder, total_pages, prefix, current_page, adjust)

		# Кнопка назад
		builder.add(InlineKeyboardButton(text="◀ Вернуться Назад", callback_data="admin_channels"))
		adjust.append(1)

		builder.adjust(*adjust)
		return builder.as_markup()

	def users_list(self, users: List[Tuple[str, str]], current_page: int, total_pages: int, prefix: str):
		"""Клавиатура со списком пользователей и пагинацией"""
		builder = InlineKeyboardBuilder()
		adjust = []
		times, empty_button = divmod(len(users), 2)
		for i in range(len(users) - 1):
			adjust.append(2)
		if empty_button:
			adjust.append(2)

		# Кнопки аользователей
		for text, callback_data in users:
			builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))

		if empty_button:
			builder.add(InlineKeyboardButton(text="_", callback_data="_"))

		# Кнопки пагинации
		self._add_pagination_buttons(builder, total_pages, prefix, current_page, adjust)

		# Кнопка назад
		builder.add(InlineKeyboardButton(text="◀ Вернуться Назад", callback_data="admin_channels"))
		adjust.append(1)

		builder.adjust(*adjust)
		return builder.as_markup()

	@staticmethod
	def _add_pagination_buttons(builder, total_pages, prefix, current_page, adjust):
		# Кнопки пагинации
		pagination_buttons = []

		if total_pages > 1:
			if current_page > 1:
				pagination_buttons.append(("⬅️ Назад", f"{prefix}_page_{current_page - 1}"))

			pagination_buttons.append((f"{current_page}/{total_pages}", "current_page"))

			if current_page < total_pages:
				pagination_buttons.append(("➡️ Вперед", f"{prefix}_page_{current_page + 1}"))

			for text, callback_data in pagination_buttons:
				builder.add(InlineKeyboardButton(text=text, callback_data=callback_data))

			adjust.append(3)

		return pagination_buttons

	@staticmethod
	def admin_channel():
		builder = InlineKeyboardBuilder()
		builder.button(text="Настроить основной/резервный канал", callback_data="admin_channels")
		return builder.as_markup()