from calendar import Calendar
from datetime import datetime
from typing import List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import Config
from tg_bot.misc.utils import localization


class SavedDriver(CallbackData, prefix="sd"):
    action: str
    driver_id: int


class CustomInlineMarkups:

    @staticmethod
    async def year(from_year: int, lang: str) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for year, counter in zip(range(from_year, from_year + 26), range(25)):
            if counter % 5 == 0:
                markup.inline_keyboard.append([])

            text = str(year) if year >= 1950 else "  "
            cd = str(year) if year >= 1950 else "0"
            markup.inline_keyboard[-1].append(InlineKeyboardButton(text=text, callback_data=cd))

        markup.inline_keyboard.append([
            InlineKeyboardButton(text="⬅️", callback_data=f"left:{from_year}"),
            InlineKeyboardButton(text="➡️", callback_data=f"right:{from_year}")
        ])

        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        btn_text = lang_data["markups"]["inline"]["additional_buttons"]["back"]
        markup.inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data="back")])

        return markup

    @staticmethod
    async def calendar(date_time: datetime, lang: str) -> InlineKeyboardMarkup:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        calendar_localization = lang_data["misc"]["calendar"]

        markup = InlineKeyboardMarkup(inline_keyboard=[])
        markup.inline_keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data="0") for btn_text in calendar_localization["weekdays"]])

        today = datetime.now(tz=Config.TIMEZONE)

        month_days = list(Calendar().itermonthdays(year=date_time.year, month=date_time.month))
        for day, counter in zip(month_days, range(len(month_days))):
            if counter % 7 == 0:
                markup.inline_keyboard.append([])

            if (day == 0) or (
                    (today.year == date_time.year and today.month == date_time.month) and day < date_time.day):
                new_btn = InlineKeyboardButton(text=" ", callback_data="0")

            else:
                new_btn = InlineKeyboardButton(text=str(day), callback_data=f"{day}.{date_time.month}.{date_time.year}")

            markup.inline_keyboard[-1].append(new_btn)

        temp_month = date_time.month + 1
        temp_year = date_time.year

        if temp_month > 12:
            temp_month = 1
            temp_year += 1

        right = InlineKeyboardButton(text="🔜", callback_data=f"r:1.{temp_month}.{temp_year}")

        # For button - Previous Month
        if date_time.month == today.month and date_time.year == today.year:
            left_cd = "0"

        else:
            temp_month = date_time.month - 1
            temp_year = date_time.year

            if temp_month < 1:
                temp_month = 12
                temp_year -= 1

            left_cd = f"l:1.{temp_month}.{temp_year}"

        left = InlineKeyboardButton(text="🔙", callback_data=left_cd)

        month = calendar_localization["months"][date_time.month - 1]
        current_month = InlineKeyboardButton(text=f"{month} {date_time.year}", callback_data="0")

        markup.inline_keyboard.append([left, current_month, right])

        back_btn_text = lang_data["markups"]["inline"]["additional_buttons"]["back"]
        markup.inline_keyboard.append([InlineKeyboardButton(text=back_btn_text, callback_data="back")])

        return markup

    @staticmethod
    async def payment(invoice_url: str, lang: str) -> InlineKeyboardMarkup:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        payment_localize = lang_data["misc"]["payment"]

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=payment_localize["invoice_url"], web_app=WebAppInfo(url=invoice_url))
                ],
                [
                    InlineKeyboardButton(text=payment_localize["cancel"], callback_data="cancel")
                ]
            ]
        )

    @staticmethod
    async def saved_driver_menu(driver_id: int, lang: str) -> InlineKeyboardMarkup:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        menu_localize = lang_data["misc"]["saved_driver"]

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=menu_localize["remove_from_notes"],
                        callback_data=SavedDriver(action="remove_from_notes", driver_id=driver_id).pack()
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=menu_localize["open_driver"],
                        callback_data=SavedDriver(action="open_driver", driver_id=driver_id).pack()
                    )
                ]
            ]
        )

    @staticmethod
    async def selectors(lang: str, data: List[str], selector_key: str, from_filter: bool = False
                        ) -> InlineKeyboardMarkup:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        loc_selector = lang_data["misc"]["selectors"][selector_key]
        loc_rows, loc_cols = loc_selector["rows"], loc_selector["cols"]

        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for row_key, row_value in zip(loc_rows.keys(), loc_rows.values()):
            el_col = "0"
            for el in data:
                if row_key in el:
                    el_col = el.split(":")[-1]
                    break

            markup.inline_keyboard.append([
                InlineKeyboardButton(text=row_value, callback_data="0"),
                InlineKeyboardButton(
                    text=loc_cols["0"] if from_filter else loc_cols[el_col], callback_data=f"{row_key}:set_value"
                )
            ])

        markup.inline_keyboard.append([
            InlineKeyboardButton(text=lang_data["markups"]["inline"]["additional_buttons"]["confirm"],
                                 callback_data="confirm")
        ])

        markup.inline_keyboard.append([
            InlineKeyboardButton(text=lang_data["misc"]["selectors"]["back"], callback_data="back")
        ])

        return markup

    @staticmethod
    async def selector_cols(lang: str, selector_key: str, current_selector_row: str) -> InlineKeyboardMarkup:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        loc_cols = lang_data["misc"]["selectors"][selector_key]["cols"]

        markup = InlineKeyboardMarkup(inline_keyboard=[])
        for key, value in zip(loc_cols.keys(), loc_cols.values()):
            if key == "0":
                continue

            markup.inline_keyboard.append([
                InlineKeyboardButton(text=value, callback_data=f"{current_selector_row}:{key}")
            ])

        markup.inline_keyboard.append([
            InlineKeyboardButton(text=lang_data["misc"]["selectors"]["back_to_menu"], callback_data="back_to_menu")
        ])

        markup.inline_keyboard.append([
            InlineKeyboardButton(text=lang_data["misc"]["selectors"]["back"], callback_data="back")
        ])

        return markup

    @staticmethod
    async def support_btn(lang: str) -> InlineKeyboardMarkup:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        markup_data = lang_data["misc"]["support"]

        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=markup_data, url=f"https://t.me/{Config.SUPPORT_USERNAME}")
                ]
            ]
        )
