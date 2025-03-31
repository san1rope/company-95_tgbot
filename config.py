import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from pytz import timezone

load_dotenv(dotenv_path=os.path.abspath(".env"))


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN").strip()
    BOT = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    DISPATCHER = Dispatcher(storage=MemoryStorage())
    ADMINS = list(map(int, os.getenv("ADMINS").strip().split(",")))
    TIMEZONE = timezone(os.getenv("TIMEZONE"))
    DEFAULT_LANG = os.getenv("DEFAULT_LANG").strip()
    SALARY_MIN = float(os.getenv("SALARY_MIN").strip())
    SALARY_MAX = float(os.getenv("SALARY_MAX").strip())
    BASE_FORM_PRICE = float(os.getenv("BASE_FORM_PRICE").strip())

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY").strip()

    DATABASE_CLEANUP = bool(int(os.getenv("DATABASE_CLEANUP")))
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
