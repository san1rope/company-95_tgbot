import logging

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from tg_bot.handlers.driver.register_driver import RegistrationSteps
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import DriverRegistration
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(DriverRegistration.ChooseBasisOfStay, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.Availability95Code, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseDateReadyToStartWork, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.IndicateLanguageSkills, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.IndicateJobExperience, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseNeedInternship, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseUnsuitableCountries, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseDangerousGoods, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.WriteExpectedSalary, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseAvailabilityCategories, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseCountryDrivingLicense, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseCountryCurrentLiving, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseWorkType, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.WriteCadence, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseCrew, F.data == "hid_or_open_form")
@router.callback_query(DriverRegistration.ChooseGender, F.data == "hid_or_open_form")
async def hid_and_open_driver_form(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    uid = callback.from_user.id
    await Ut.handler_log(logger, uid)

    data = await state.get_data()
    data_model = data["dmodel"]
    title = data["title"]
    markup = data["markup"]
    saved_data = data["saved_data"] if "saved_data" in data else None
    lang = await RegistrationSteps.get_lang(state_data=data, user_id=uid)
    hidden_status = data["hidden_status"] if data.get("hidden_status") else False

    if hidden_status:
        hidden_status = False

    else:
        hidden_status = True

    await state.update_data(hidden_status=hidden_status)
    markup = await Ut.get_markup(lang=lang, markup=markup, hidden_status=hidden_status)
    if saved_data:
        markup = await Ut.recognize_selected_values(
            markup=markup, datalist=data["saved_data"],
            text_placeholder="🟢" if ':' in saved_data[0] else "✅ %btn.text%")

    text = await DriverForm().form_completion(title=title, lang=lang, db_model=data_model, hidden_status=hidden_status)
    await callback.message.edit_text(text=text, reply_markup=markup)
