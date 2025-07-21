from typing import Optional

from aiogram import types


def extract_channel_info(message: types.Message) -> Optional[dict]:
	"""Извлечение информации о канале из пересланного сообщения"""
	if not message.forward_from_chat:
		return None

	chat = message.forward_from_chat
	if chat.type not in ('channel', 'group', 'supergroup'):
		return None

	return {
		'id': chat.id,
		'title': chat.title,
		'username': chat.username,
		'type': chat.type
	}
