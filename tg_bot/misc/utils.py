import asyncio
import logging
import re
import os
import json
from copy import deepcopy
from logging import Logger
from typing import Union, Optional, Dict, List

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from pydantic import BaseModel

from config import Config

logger = logging.getLogger(__name__)
localization: Dict[str, Dict] = {}
corrections: Dict[str, Dict[str, float]] = {}
msg_to_delete = {"secondary": {}}
call_functions = {}


class AdditionalButtons(BaseModel):
    index: Optional[int] = None
    action: str = "exist"
    buttons: Dict[str, Optional[int]]


class Utils:

    @staticmethod
    def wrapper(func, *args):
        asyncio.run(func(*args))

    @staticmethod
    async def handler_log(logger_from_caller: Logger, user_id: Union[str, int]):
        logger_from_caller.info(f"Handler called. user_id={user_id}")

    @staticmethod
    async def load_localizations_files():
        localization_folder = "tg_bot/misc/localization/"
        for filename in os.listdir(os.path.abspath(localization_folder)):
            lang = filename.replace(".json", "")
            with open(os.path.abspath(localization_folder + filename), "r", encoding="utf-8") as file:
                data = json.load(file)

            localization.update({lang: data})

        corrections_file = "tg_bot/misc/corrections.json"
        with open(os.path.abspath(corrections_file), "r", encoding="utf-8") as file:
            corrections.update(json.load(file))

    @staticmethod
    async def send_step_message(user_id: int, texts: List[str], markups: List[InlineKeyboardMarkup] = None):
        await Utils.delete_messages(user_id=user_id)

        messages = []
        for text, counter in zip(texts, range(len(texts))):
            if not text:
                continue

            try:
                if markups:
                    markup = markups[counter]

                else:
                    markup = None

            except IndexError:
                markup = None

            msg = await Config.BOT.send_message(chat_id=user_id, text=text, reply_markup=markup)
            await Utils.add_msg_to_delete(user_id=user_id, msg_id=msg.message_id)

            messages.append(msg)

        return messages

    @staticmethod
    async def get_message_text(key: str, lang: str) -> str:
        lang_data = localization[lang] if localization.get(lang) else localization[Config.DEFAULT_LANG]
        return "\n".join(lang_data["messages"][key])

    @staticmethod
    async def processing_additional_buttons(
            markup_data: Dict, markup: InlineKeyboardMarkup, additional_buttons: List[AdditionalButtons] = []):
        for add_buttons_obj in additional_buttons:
            if (not (add_buttons_obj.index is None)) and add_buttons_obj.action == "new":
                markup.inline_keyboard.insert(add_buttons_obj.index, [])
                add_buttons_obj.index -= 1

            elif add_buttons_obj.index is None:
                markup.inline_keyboard.append([])

            for btn_key, btn_index in add_buttons_obj.buttons.items():
                btn_text = markup_data["markups"]["inline"]["additional_buttons"][btn_key]
                btn_key = btn_key[:btn_key.find(":")] if btn_key.find(":") != -1 else btn_key
                btn_obj = InlineKeyboardButton(text=btn_text, callback_data=btn_key)

                row_ind_bool = not (add_buttons_obj.index is None)
                btn_ind_bool = not (btn_index is None)
                if row_ind_bool and btn_ind_bool:
                    markup.inline_keyboard[add_buttons_obj.index].insert(btn_index, btn_obj)

                elif row_ind_bool and (not btn_ind_bool):
                    markup.inline_keyboard[add_buttons_obj.index].append(btn_obj)

                elif (not row_ind_bool) and btn_ind_bool:
                    markup.inline_keyboard[-1].insert(btn_index, btn_obj)

                else:
                    markup.inline_keyboard[-1].append(btn_obj)

        return markup

    @classmethod
    async def get_markup(
            cls, lang: str, mtype: Optional[str] = None, key: Optional[str] = None,
            additional_buttons: List[AdditionalButtons] = [], without_buttons: List[str] = [],
            user_id: Union[str, int] = None, markup: Optional[InlineKeyboardMarkup] = None
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
                                callback_data in without_buttons):
                            continue

                        new_btn = InlineKeyboardButton(text=btn_text.replace("&a|", ""), callback_data=callback_data)
                        markup.inline_keyboard[-1].append(new_btn)

            else:
                logger.error(f"Incorrect mtype parameter! mtype={mtype}; key={key}; lang={lang}; user_id={user_id}")
                return

            if additional_buttons:
                if isinstance(markup, InlineKeyboardMarkup):
                    markup = await cls.processing_additional_buttons(
                        markup_data=markup_data, markup=markup, additional_buttons=additional_buttons)

                elif isinstance(markup, ReplyKeyboardMarkup):
                    markup.keyboard.append([KeyboardButton(text=btn_text)])

        elif additional_buttons:
            markup = InlineKeyboardMarkup(inline_keyboard=[])
            markup = await cls.processing_additional_buttons(
                markup_data=markup_data, markup=markup, additional_buttons=additional_buttons)

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
