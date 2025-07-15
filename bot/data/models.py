# Модели данных

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    id: int
    username: Optional[str]
    full_name: str
    is_active: bool = True
    is_banned: bool = False
    captcha_passed: bool = False
    should_notify: bool = True  # Получать уведомления о смене канала
    join_date: datetime = datetime.now()

@dataclass
class Channel:
    id: int
    title: str
    username: Optional[str]
    is_main: bool = False
    is_backup: bool = False

@dataclass
class Admin:
    user_id: int
    username: Optional[str]
    full_name: str
    level: int = 1  # Уровень доступа (1 - базовый, 2 - полный)
    created_at: datetime = datetime.now()

@dataclass
class Captcha:
    user_id: int
    text: str
    attempts: int = 0 # При трех не правильных попытках банить вход на 5 мин
    created_at: datetime = datetime.now()