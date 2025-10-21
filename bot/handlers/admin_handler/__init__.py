from aiogram import Router

from .chat_handler import router as chat_router
from .main_handler import router as main_router
from .stats_handler import router as stats_router
from .users_handler import router as users_router
from .channels_handler import router as channels_router
from .notification_handler import router as notification_router
from .welcome_handler import router as welcome_router
from .broadcast_handler import router as broadcast_router


router = Router(name=__name__)

router.include_routers(
channels_router,
main_router,
stats_router,
users_router,
notification_router,
welcome_router,
broadcast_router,
chat_router
)
