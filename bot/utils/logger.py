import logging
import sys
from pathlib import Path
from typing import Optional


class BotLogger:
	def __init__(self, name: str, log_file: Optional[str] = "bot.log"):
		self.logger = logging.getLogger(name)
		self.logger.setLevel(logging.INFO)

		formatter = logging.Formatter(
			'%(asctime)s - %(name)s - %(levelname)s - %(message)s',
			datefmt='%Y-%m-%d %H:%M:%S'
		)

		# Консольный вывод
		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(formatter)

		# Файловый вывод
		if log_file:
			log_dir = Path("logs")
			log_dir.mkdir(exist_ok=True)
			file_handler = logging.FileHandler(log_dir / log_file)
			file_handler.setFormatter(formatter)
			self.logger.addHandler(file_handler)

		self.logger.addHandler(console_handler)

	def get_logger(self):
		return self.logger


# Инициализация глобального логгера
logger = BotLogger("main_bot").get_logger()