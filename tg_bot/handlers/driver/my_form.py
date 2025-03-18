import asyncio
import logging
from typing import Union, Optional

import stripe
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbDriver
from tg_bot.handlers.driver.menu import show_menu
from tg_bot.handlers.driver.register_driver import RegistrationSteps
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import DriverFormStates
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "driver_my_form")
async def show_my_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    driver = await DbDriver(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="driver_menu_my_form", lang=driver.lang)
    text = await DriverForm().form_completion(db_model=driver, title=text, lang=driver.lang)
    markup = await Ut.get_markup(mtype="inline", lang=driver.lang, key="driver_menu_my_form")
    await Ut.send_step_message(user_id=uid, text=text, markup=markup)

    await state.set_state(DriverFormStates.ChooseAction)


@router.callback_query(DriverFormStates.ChooseAction)
async def form_reset_confirmation(callback: Optional[Union[types.CallbackQuery, int]], state: FSMContext,
                                  from_reg_steps: bool = False):
    if isinstance(callback, types.CallbackQuery):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        cd = callback.data

    else:
        uid = callback
        cd = ""

    driver = await DbDriver(tg_user_id=uid).select()
    if cd == "driver_my_form_reset":
        text = await Ut.get_message_text(key="driver_menu_my_form_reset_confirmation", lang=driver.lang)
        markup = await Ut.get_markup(mtype="inline", lang=driver.lang, key="confirmation")
        await Ut.send_step_message(user_id=uid, text=text, markup=markup)

        await state.set_state(DriverFormStates.FormResetConfirmation)

    elif cd == "driver_my_form_change" or from_reg_steps:
        text = await Ut.get_message_text(key="driver_menu_my_form_choose_field", lang=driver.lang)
        markup = await Ut.get_markup(mtype="inline", lang=driver.lang, key="driver_menu_my_form_change_options_list")
        await Ut.delete_messages(user_id=uid)

        if isinstance(callback, types.CallbackQuery):
            msg = await callback.message.answer(text=text, reply_markup=markup)

        else:
            msg = await Config.BOT.send_message(chat_id=uid, text=text, reply_markup=markup)

        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

        await state.set_state(DriverFormStates.ChooseFieldToEdit)

    elif cd == "back":
        await state.clear()
        await show_menu(message=callback)


@router.callback_query(DriverFormStates.FormResetConfirmation)
async def form_reset_finish(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    driver = await DbDriver(tg_user_id=uid).select()

    cd = callback.data
    if cd == "confirm":
        result = await DbDriver(tg_user_id=uid).remove()
        if result:
            text = await Ut.get_message_text(key="driver_menu_my_form_reset_completed", lang=driver.lang)
            await Ut.delete_messages(user_id=uid)
            await state.clear()

        else:
            text = await Ut.get_message_text(key="driver_menu_my_form_reset_error", lang=driver.lang)

        msg = await callback.message.answer(text=text)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    elif cd == "back":
        await state.clear()
        return await show_my_form(callback=callback, state=state)


@router.callback_query(DriverFormStates.ChooseFieldToEdit)
async def field_selected(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    driver = await DbDriver(tg_user_id=uid).select()

    cd = callback.data
    if cd == "back":
        return await show_my_form(callback=callback, state=state)

    await state.update_data(status=1, function_for_back=form_reset_confirmation, call_function=field_has_changed)

    reg_method = getattr(RegistrationSteps, cd)
    await reg_method(state=state, lang=driver.lang)


async def field_has_changed(state: FSMContext, returned_data: Union[str, int], field_name: str):
    tg_user_id = state.key.user_id
    await Ut.handler_log(logger, tg_user_id)

    driver = await DbDriver(tg_user_id=tg_user_id).select()

    form_price = await DriverForm().calculate_form_data(db_model=driver)

    if driver.stripe_price_id:
        await stripe.Price.modify_async(id=driver.stripe_price_id, active=False)

    price = None
    if driver.stripe_product_id:
        price = await stripe.Price.create_async(
            product=driver.stripe_product_id, unit_amount=int(form_price * 100), currency="pln")

    result = await DbDriver(tg_user_id=tg_user_id).update(
        opens_count=0, form_price=form_price, stripe_price_id=price.id if price else None, **{field_name: returned_data}
    )
    if result:
        text = await Ut.get_message_text(key="driver_menu_my_form_param_changed", lang=driver.lang)
        await Ut.send_step_message(user_id=tg_user_id, text=text)

        await asyncio.sleep(1)

        await form_reset_confirmation(callback=tg_user_id, state=state, from_reg_steps=True)

    else:
        text = await Ut.get_message_text(key="driver_menu_my_form_error_param_change", lang=driver.lang)
        msg = await Config.BOT.send_message(chat_id=tg_user_id, text=text)
        await Ut.add_msg_to_delete(user_id=tg_user_id, msg_id=msg.message_id)
