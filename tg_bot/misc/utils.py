import logging
import re
from logging import Logger
from typing import Union, Optional, Dict, List

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton

from config import Config

logger = logging.getLogger(__name__)
localization: Dict[str, Dict] = {}
corrections: Dict[str, Dict[str, float]] = {}
msg_to_delete = {"secondary": {}}
call_functions = {}


class Utils:

    @staticmethod
    async def handler_log(logger_from_caller: Logger, user_id: Union[str, int]):
        logger_from_caller.info(f"Handler called. user_id={user_id}")

    @staticmethod
    async def send_step_message(user_id: int, text: str, markup: Optional[InlineKeyboardMarkup] = None):
        await Utils.delete_messages(user_id=user_id)
        msg = await Config.BOT.send_message(chat_id=user_id, text=text, reply_markup=markup)
        await Utils.add_msg_to_delete(user_id=user_id, msg_id=msg.message_id)

    @staticmethod
    async def get_message_text(key: str, lang: str) -> str:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        return "\n".join(lang_data["messages"][key])

    @staticmethod
    async def get_markup(
            mtype: str, lang: str, key: Optional[str] = None, add_btn: Optional[str] = None,
            add_btn_index: Optional[int] = None, without_inline_buttons: List = [], user_id: Union[str, int] = None
    ) -> Union[ReplyKeyboardMarkup, InlineKeyboardMarkup, None]:
        markup_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]

        if key:
            buttons_list = markup_data["markups"][mtype][key]
            if mtype == "default":
                markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[])
                for row in buttons_list:
                    markup.keyboard.append([])
                    for btn_text in row:
                        if "&a|" in btn_text and user_id not in Config.ADMINS:
                            continue

                        markup.keyboard[-1].append(KeyboardButton(text=btn_text.replace("&a|", "")))

            elif mtype == "inline":
                markup = InlineKeyboardMarkup(inline_keyboard=[])
                for row in buttons_list:
                    markup.inline_keyboard.append([])
                    for btn_text, callback_data in row.items():
                        if (("&a|" in btn_text) and (user_id not in Config.ADMINS)) or (
                                callback_data in without_inline_buttons):
                            continue

                        new_btn = InlineKeyboardButton(text=btn_text.replace("&a|", ""), callback_data=callback_data)
                        markup.inline_keyboard[-1].append(new_btn)

            else:
                logger.error(f"Incorrect mtype parameter! mtype={mtype}; key={key}; lang={lang}; user_id={user_id}")
                return

            if add_btn:
                btn_text = markup_data["markups"][mtype]["additional_buttons"][add_btn]
                if isinstance(markup, InlineKeyboardMarkup):
                    callback_data = add_btn[:add_btn.find(":")] if add_btn.find(":") != -1 else add_btn
                    btn = InlineKeyboardButton(text=btn_text, callback_data=callback_data)
                    if add_btn_index:
                        markup.inline_keyboard.insert(add_btn_index, [btn])

                    else:
                        markup.inline_keyboard.append([btn])

                elif isinstance(markup, ReplyKeyboardMarkup):
                    markup.keyboard.append([KeyboardButton(text=btn_text)])

        elif add_btn:
            btn_text = markup_data["markups"][mtype]["additional_buttons"][add_btn]
            markup = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text=btn_text, callback_data=add_btn)]])

        else:
            markup = InlineKeyboardMarkup(inline_keyboard=[])

        return markup

    @staticmethod
    async def recognize_selected_values(markup: InlineKeyboardMarkup, datalist: List[str], text_placeholder: str):
        for row in markup.inline_keyboard:
            for btn in row:
                if btn.callback_data in datalist:
                    btn.text = text_placeholder.replace("%btn.text%", btn.text)

        return markup

    @staticmethod
    async def add_msg_to_delete(user_id: Union[str, int], msg_id: Union[str, int], secondary: bool = False):
        try:
            if secondary:
                if user_id not in msg_to_delete["secondary"]:
                    msg_to_delete["secondary"][user_id] = []

                msg_to_delete["secondary"][user_id].append(msg_id)
                return

            if user_id not in msg_to_delete:
                msg_to_delete[user_id] = []

            msg_to_delete[user_id].append(msg_id)

        except Exception as ex:
            logger.error(f"Couldn't add msg_id to msg_to_delete\n{ex}")

    @staticmethod
    async def delete_messages(user_id: Optional[int] = None, secondary: bool = False):
        try:
            if not user_id:
                for uid in msg_to_delete:
                    for msg_id in msg_to_delete.get(uid):
                        try:
                            await Config.BOT.delete_message(chat_id=uid, message_id=msg_id)
                        except TelegramBadRequest:
                            continue

                return

            if secondary:
                for msg_id in msg_to_delete["secondary"][user_id]:
                    try:
                        await Config.BOT.delete_message(chat_id=user_id, message_id=msg_id)
                    except TelegramBadRequest:
                        continue

            else:
                for msg_id in msg_to_delete[user_id]:
                    try:
                        await Config.BOT.delete_message(chat_id=user_id, message_id=msg_id)
                    except TelegramBadRequest:
                        continue

            msg_to_delete[user_id].clear()
        except KeyError:
            return

    @staticmethod
    async def is_valid_name(name: str) -> bool:
        return bool(re.match(r"^[A-Za-z\s']+$", name))

    @staticmethod
    async def is_number(value: str):
        return bool(re.fullmatch(r"-?\d+(\.\d+)?", value))
