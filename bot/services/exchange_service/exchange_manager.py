from ...utils.loggers import services as logger

class ExchangeManager:
	def __init__(self):
		self.exchanges = {
			"binance": BinanceAPI(),
			"bybit": BybitAPI(),
			"kucoin": KucoinAPI()
		}

	async def get_rates(self, from_currency: str, to_currency: str) -> dict:
		"""Получение курсов от всех бирж"""
		rates = {}
		for name, api in self.exchanges.items():
			try:
				rate = await api.get_rate(from_currency, to_currency)
				rates[name] = rate
			except Exception as e:
				logger.error(f"Error getting rate from {name}: {e}")
		return rates