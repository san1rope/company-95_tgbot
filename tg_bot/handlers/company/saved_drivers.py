import logging
import asyncio
from math import ceil

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.handlers.company.menu import show_menu
from tg_bot.keyboards.inline import saved_driver_menu_inline, SavedDriver
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import CompanySavedDrivers
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "saved_drivers")
@router.callback_query(CompanySavedDrivers.Actions, F.data == "prev_page")
@router.callback_query(CompanySavedDrivers.Actions, F.data == "next_page")
@router.callback_query(CompanySavedDrivers.Actions, F.data == "back")
async def show_saved_drivers(callback: types.CallbackQuery, state: FSMContext, from_back_btn: bool = False):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    cd = callback.data
    if cd == "back" and not from_back_btn:
        await state.clear()
        return await show_menu(message=callback)

    company = await DbCompany(tg_user_id=uid).select()
    if not company.saved_drivers:
        text = await Ut.get_message_text(lang=company.lang, key="no_saved_drivers")
        await Ut.send_step_message(user_id=uid, text=text)
        await asyncio.sleep(1.5)
        return await show_menu(message=callback)

    data = await state.get_data()
    num_of_pages = data["num_of_pages"] if data.get("num_of_pages") else ceil(len(company.saved_drivers) / 3)
    curr_page = data.get("curr_page")
    if curr_page is None:
        curr_page = 1
        await state.update_data(curr_page=1, num_of_pages=num_of_pages)

    elif cd == "next_page":
        curr_page += 1
        if curr_page > num_of_pages:
            return

        await state.update_data(curr_page=curr_page)

    elif cd == "prev_page":
        curr_page -= 1
        if curr_page <= 0:
            return

        await state.update_data(curr_page=curr_page)

    text_your_drivers = await Ut.get_message_text(key="your_saved_drivers", lang=company.lang)
    text_your_drivers = text_your_drivers.replace("%curr_page%", str(curr_page))
    text_your_drivers = text_your_drivers.replace("%num_of_pages%", str(num_of_pages))
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="saved_and_opened_drivers_menu")

    drivers_texts = []
    start_index = 3 * (curr_page - 1)
    for driver_id in company.saved_drivers[start_index:start_index + 3]:
        driver = await DbDriver(db_id=driver_id).select()
        title = f"<b>🆔 Водитель №{driver.id}</b>"
        d_text = await DriverForm().form_completion(title=title, lang=company.lang, db_model=driver, for_company=True)
        d_markup = await saved_driver_menu_inline(driver_id=driver_id, lang=company.lang)
        drivers_texts.append([d_text, d_markup])

    await Ut.send_step_message(user_id=uid, text=text_your_drivers, markup=markup)
    for msg_data in drivers_texts:
        d_text, d_markup = msg_data
        msg = await callback.message.answer(text=d_text, reply_markup=d_markup)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(CompanySavedDrivers.Actions)


@router.callback_query(CompanySavedDrivers.Actions, SavedDriver.filter(F.action == "remove_from_notes"))
async def driver_remove_from_notes(callback: types.CallbackQuery, state: FSMContext, callback_data: SavedDriver):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    await state.update_data(current_driver_id=callback_data.driver_id)
    company = await DbCompany(tg_user_id=uid).select()

    text = await Ut.get_message_text(key="driver_remove_from_notes", lang=company.lang)
    text = text.replace("%driver_id%", str(callback_data.driver_id))
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="confirmation")
    await Ut.send_step_message(text=text, markup=markup, user_id=uid)

    await state.set_state(CompanySavedDrivers.RemoveConfirmation)


@router.callback_query(CompanySavedDrivers.RemoveConfirmation)
async def remove_driver_from_saved_list(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    cd = callback.data
    if cd == "confirm":
        data = await state.get_data()
        current_driver_id = data["current_driver_id"]
        curr_page = data["curr_page"]

        company = await DbCompany(tg_user_id=uid).select()
        company.saved_drivers.remove(current_driver_id)
        num_of_pages = ceil(len(company.saved_drivers) / 3)
        await state.update_data(
            num_of_pages=num_of_pages, curr_page=curr_page if curr_page <= num_of_pages else num_of_pages)
        await DbCompany(db_id=company.id).update(saved_drivers=company.saved_drivers)

        text = await Ut.get_message_text(key="driver_remove_from_notes_confirm", lang=company.lang)
        await Ut.send_step_message(user_id=uid, text=text)
        await asyncio.sleep(1.5)

    await show_saved_drivers(callback=callback, state=state, from_back_btn=True)


@router.callback_query(CompanySavedDrivers.Actions, F.data == "open_driver")
async def driver_open(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)


