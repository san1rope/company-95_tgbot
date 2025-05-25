import logging

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany
from tg_bot.handlers.company.menu import show_menu
from tg_bot.handlers.company.payments_processing import PaymentsProcessing
from tg_bot.misc.states import CompanySubscription
from tg_bot.misc.utils import Utils as Ut, AdditionalButtons

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "buy_subscription")
async def show_subscription_info(callback: types.CallbackQuery, state: FSMContext, from_payment_cancel: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    company = await DbCompany(tg_user_id=uid).select()

    if company.paid_subscription:
        text = await Ut.get_message_text(lang=company.lang, key="company_already_has_subscription_info")
        text = text.replace("%opens_count%", str(company.paid_subscription))
        markup = await Ut.get_markup(
            mtype="inline", lang=company.lang, additional_buttons=[AdditionalButtons(buttons={"back": None})]
        )

    else:
        text = await Ut.get_message_text(lang=company.lang, key="company_subscription_info")
        markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="company_choose_payment_system")

    await Ut.send_step_message(user_id=uid, texts=[text], markups=[markup])

    await state.set_state(CompanySubscription.ChoosePaymentSystem)


@router.callback_query(CompanySubscription.ChoosePaymentSystem)
async def call_payment_method(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    cd = callback.data
    if cd == "back":
        return await show_menu(message=callback)

    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(lang=company.lang, key="payment_in_creating_process")
    await Ut.send_step_message(user_id=uid, texts=[text])

    await state.update_data(function_for_back=show_subscription_info, type="subscribe")

    payment_method = getattr(PaymentsProcessing, cd)
    await payment_method(callback=callback, state=state)
