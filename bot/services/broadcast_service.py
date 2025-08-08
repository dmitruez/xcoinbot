from datetime import datetime
from typing import List, Tuple, Optional, Dict

from ..repositories import AdminRepository
from ..repositories.broadcast_repository import BroadcastRepository
from ..models import BroadcastMessage, Button
from ..utils.work_with_date import get_datetime_now


class BroadcastService:
	def __init__(self, broadcast_repository: BroadcastRepository, admin_repository: AdminRepository):
		self.repository = broadcast_repository
		self.admin_repository = admin_repository
	
	async def save_broadcast(
			self,
			text: str,
			media_type: str,
			media_id: Optional[str],
			buttons: List[Button],
			sent_by: int,
			total_users: int
	) -> int:
		"""Сохранение информации о рассылке"""
		broadcast = BroadcastMessage(
			text=text,
			media_type=media_type,
			media_id=media_id,
			buttons=buttons,
			sent_at=get_datetime_now(),
			sent_by=sent_by,
			total_users=total_users
		)
		return await self.repository.create(broadcast)
	
	async def update_broadcast_stats(
			self,
			broadcast_id: int,
			success: int,
			errors: int
	) -> None:
		"""Обновление статистики рассылки"""
		await self.repository.update_stats(broadcast_id, success, errors)
	
	async def get_broadcast_by_id(self, broadcast_id: int) -> Optional[BroadcastMessage]:
		"""Получение рассылки по ID"""
		return await self.repository.get_by_id(broadcast_id)
	
	async def get_broadcast_history(self, limit: int = 10) -> List[BroadcastMessage]:
		"""Получение истории рассылок"""
		return await self.repository.get_history(limit)
	
	async def format_broadcast_stats(self, broadcast: BroadcastMessage) -> str:
		"""Форматирование статистики рассылки"""
		
		admin = await self.admin_repository.get(broadcast.sent_by)
		
		buttons_info = ""
		for btn in broadcast.buttons:
			if btn.button_type == "url":
				buttons_info += f"🔗 {btn.text}: {btn.value}\n"
			else:
				buttons_info += f"💬 {btn.text}: {btn.value[:30]}...\n"
		 
		text = (
			f"📊 <b>Детали рассылки #{broadcast.id}</b>\n\n"
			f"📅 Дата: {broadcast.sent_at.strftime('%d.%m.%Y %H:%M')}\n"
			f"👤 Администратор: <a href='tg://user?id={broadcast.sent_by}'>{admin.full_name}</a>\n"
			f"✅ Успешно: {broadcast.success_count}\n"
			f"❌ Ошибок: {broadcast.error_count}\n"
			f"👥 Всего получателей: {broadcast.total_users}\n"
			f"📈 Процент доставки: {self._delivery_rate(broadcast)}%\n\n"
			f"🔘 <b>Кнопки:</b>\n{buttons_info if buttons_info else 'Нет кнопок'}\n\n"
			f"📝 <b>Содержание:</b>\n{broadcast.text[:300]}..."
		)
		
		return text
	
	
	@staticmethod
	def _delivery_rate(broadcast: BroadcastMessage) -> float:
		"""Расчет процента доставки"""
		if broadcast.total_users == 0:
			return 0.0
		return round((broadcast.success_count / broadcast.total_users) * 100, 2)
	
	
	