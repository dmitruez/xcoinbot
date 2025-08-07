import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, types
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .message_service import MessageService
from ..models import Channel, MessageTemplate, Button
from ..repositories import Repositories
from ..utils.loggers import services as logger


class WelcomeService(MessageService):
	TEMPLATE_FILE = "welcome_template.json"
	
	def __init__(self, bot: Bot, repos: Repositories):
		super().__init__(bot, repos, 'welcome', '👋 Добро пожаловать!\n\nМы рады видеть вас в нашем сообществе.')
	