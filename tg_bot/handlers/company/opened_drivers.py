import asyncio
import logging
from math import ceil

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from tg_bot.db_models.quick_commands import DbCompany, DbDriver
from tg_bot.handlers.company.menu import show_menu
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import CompanyOpenedDrivers
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "bought_drivers")
@router.callback_query(CompanyOpenedDrivers.Actions)
async def show_opened_drivers(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    cd = callback.data
    if cd == "back":
        await state.clear()
        return await show_menu(message=callback)

    company = await DbCompany(tg_user_id=uid).select()
    if not company.open_drivers:
        text = await Ut.get_message_text(lang=company.lang, key="no_opened_drivers")
        await Ut.send_step_message(user_id=uid, texts=[text])
        await asyncio.sleep(1.5)
        return await show_menu(message=callback)

    data = await state.get_data()
    num_of_pages = data["num_of_pages"] if data.get("num_of_pages") else ceil(len(company.open_drivers) / 3)
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

    text_your_drivers = await Ut.get_message_text(key="your_opened_drivers", lang=company.lang)
    text_your_drivers = text_your_drivers.replace("%curr_page%", str(curr_page))
    text_your_drivers = text_your_drivers.replace("%num_of_pages%", str(num_of_pages))
    markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="saved_and_opened_drivers_menu")

    drivers_texts = []
    start_index = 3 * (curr_page - 1)
    for driver_id in company.open_drivers[start_index:start_index + 3]:
        driver = await DbDriver(db_id=driver_id).select()
        title = f"<b>🆔 Водитель №{driver.id}</b>"
        d_text = title + "\n" + await DriverForm().form_completion(lang=company.lang, db_model=driver)
        drivers_texts.append(d_text)

    await Ut.send_step_message(user_id=uid, texts=[text_your_drivers], markups=[markup])
    for d_text in drivers_texts:
        msg = await callback.message.answer(text=d_text)
        await Ut.add_msg_to_delete(user_id=uid, msg_id=msg.message_id)

    await state.set_state(CompanyOpenedDrivers.Actions)
