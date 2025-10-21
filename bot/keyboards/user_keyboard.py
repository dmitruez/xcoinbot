from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


CONTACT_ADMINS_BUTTON = "💬 Написать админам"
BACK_TO_MENU_BUTTON = "◀️ Главное меню"
USER_REPLY_CALLBACK_PREFIX = "user_reply_admin"


class UserKeyboards:
        @staticmethod
        def captcha_refresh():
                """Клавиатура для обновления капчи"""
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                        text="🔄 Обновить капчу",
                        callback_data="refresh_captcha"
                ))
                return builder.as_markup()


        @staticmethod
        def exchange_direction():
                """Клавиатура для выбора направления обмена"""
                builder = InlineKeyboardBuilder()
                builder.add(
                        InlineKeyboardButton(text="BTC → USDT", callback_data="btc_usdt"),
                        InlineKeyboardButton(text="USDT → RUB", callback_data="usdt_rub")
                )
                return builder.as_markup()

        @staticmethod
        def main_menu():
                """Главное меню пользователя"""
                builder = ReplyKeyboardBuilder()
                builder.button(text=CONTACT_ADMINS_BUTTON)
                return builder.as_markup(resize_keyboard=True)

        @staticmethod
        def chat_cancel():
                """Клавиатура отмены отправки сообщения"""
                builder = ReplyKeyboardBuilder()
                builder.button(text=BACK_TO_MENU_BUTTON)
                return builder.as_markup(resize_keyboard=True)

        @staticmethod
        def chat_reply_to_admin(admin_id: int):
                """Кнопка ответа администратору"""
                builder = InlineKeyboardBuilder()
                builder.button(
                        text="↩️ Ответить администратору",
                        callback_data=f"{USER_REPLY_CALLBACK_PREFIX}_{admin_id}"
                )
                builder.adjust(1)
                return builder.as_markup()

