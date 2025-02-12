import logging
from typing import Union

from aiogram import Router, F, types, enums
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from tg_bot.misc.states import AfterStart
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.chat.type == enums.ChatType.PRIVATE, CommandStart())
async def choose_language(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    uid = message.from_user.id
    ulang = message.from_user.language_code
    await Ut.handler_log(logger, uid)

    if isinstance(message, types.CallbackQuery):
        await message.answer()
        message = message.message

    text = await Ut.get_message_text(key="choose_lang", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="choose_lang", lang=ulang)
    await Ut.delete_messages(user_id=uid)
    msg = await message.answer(text=text, reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(AfterStart.ChooseLang)


@router.callback_query(AfterStart.ChooseLang)
async def choose_role(message: [types.CallbackQuery, types.Message], state: FSMContext):
    await message.answer()
    uid = message.from_user.id
    await Ut.handler_log(logger, uid)

    if isinstance(message, types.CallbackQuery):
        cd = message.data
        if cd == "back":
            data = await state.get_data()
            ulang = data["ulang"]

        else:
            await state.update_data(ulang=cd)
            ulang = cd

        message = message.message

    else:
        ulang = ""

    text = await Ut.get_message_text(key="choose_role", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", key="choose_role", lang=ulang, add_btn="back")
    await Ut.delete_messages(user_id=uid)
    msg = await message.answer(text=text, reply_markup=markup)
    await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(AfterStart.ChooseRole)


@router.callback_query(AfterStart.ChooseRole, F.data == "back")
async def back_from_roles(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    await choose_language(message=callback, state=state)
