from aiogram import Router, Dispatcher

from .admin_handler import router as admin_router
from .base_handler import router as base_router
from .captcha_handler import router as captcha_router
from .user_chat_handler import router as chat_router



router = Router(name=__name__)

router.include_routers(base_router, chat_router, admin_router, captcha_router)


def register_handlers(dp: Dispatcher):
	dp.include_router(router)