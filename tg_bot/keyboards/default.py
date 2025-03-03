from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import Config
from tg_bot.misc.utils import localization


async def request_contact_default(lang: str) -> ReplyKeyboardMarkup:
    markup_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [
                KeyboardButton(text=markup_data["markups"]["default"]["request_contact"][0], request_contact=True)
            ]
        ]
    )
