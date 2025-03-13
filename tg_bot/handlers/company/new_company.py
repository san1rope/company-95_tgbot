import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.handlers.company.driver_filters import processing_filters_menu
from tg_bot.misc.states import CompanyRegistration
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "company_menu")
async def motd_message(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]

    text = await Ut.get_message_text(key="company_reg_motd", lang=ulang)
    markup = await Ut.get_markup(mtype="inline", lang=ulang, key="start_search_driver")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(CompanyRegistration.MOTDMessage)


@router.callback_query(CompanyRegistration.MOTDMessage)
async def add_company_to_db(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    ulang = data["ulang"]

    cd = callback.data
    if cd == "start_search":
        company = await DbCompany(tg_user_id=uid, lang=ulang, paid_subscription=None, viewed_drivers=[]).add()
        if not company:
            text = await Ut.get_message_text(lang=ulang, key="company_add_to_db_error")
            msg = await callback.message.answer(text=text)
            return await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        return await processing_filters_menu(message=uid, state=state)
