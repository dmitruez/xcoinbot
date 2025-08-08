from datetime import datetime, timezone, timedelta
from ..config import Config

timedelta = timedelta(hours=Config.TIME_ZONE)
tz = timezone(timedelta)

def get_datetime_now() -> datetime:
	return datetime.now(tz).replace(tzinfo=None)


