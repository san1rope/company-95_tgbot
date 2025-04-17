import asyncio
import logging
from datetime import datetime

import stripe
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from stripe.oauth_error import InvalidRequestError

from config import Config
from tg_bot.db_models.db_gino import connect_to_db
from tg_bot.db_models.quick_commands import DbDriver, DbPayment, DbCompany
from tg_bot.db_models.schemas import Payment
from tg_bot.keyboards.inline import CustomInlineMarkups as Cim
from tg_bot.misc.models import DriverForm
from tg_bot.misc.states import CompanyFindDriver
from tg_bot.misc.utils import Utils as Ut

logger = logging.getLogger(__name__)
router = Router()


class PaymentsProcessing:
    STRIPE = "stripe"
    CRYPTOMUS = "cryptomus"

    PAY_FOR_DRIVER = "pay_for_driver"
    SUBSCRIPTION_FEE = "subscription_fee"

    @staticmethod
    async def stripe(callback: types.CallbackQuery, state: FSMContext):
        uid = callback.from_user.id

        data = await state.get_data()
        current_driver_id = data.get("current_driver_id")
        p_type = data["type"]

        company = await DbCompany(tg_user_id=uid).select()

        if p_type == "open_driver":
            db_type = PaymentsProcessing.PAY_FOR_DRIVER
            driver = await DbDriver(db_id=current_driver_id).select()
            try:
                if not driver.stripe_product_id:
                    raise InvalidRequestError(code="1", description="abc")

                product = await stripe.Product.retrieve_async(driver.stripe_product_id)

            except InvalidRequestError:
                product = await stripe.Product.create_async(name=f"Driver's form #{current_driver_id}")
                await DbDriver(db_id=driver.id).update(stripe_product_id=product.id)

            amount = int(driver.form_price * 100)
            try:
                if not driver.stripe_price_id:
                    raise InvalidRequestError(code="1", description="abc")

                price = await stripe.Price.retrieve_async(driver.stripe_price_id)

            except InvalidRequestError:
                price = await stripe.Price.create_async(
                    product=product.id, unit_amount=int(driver.form_price * 100), currency="pln")
                await DbDriver(db_id=driver.id).update(stripe_price_id=price.id)

        elif p_type == "subscribe":
            db_type = PaymentsProcessing.SUBSCRIPTION_FEE
            try:
                if not company.stripe_subscribe_product_id:
                    raise InvalidRequestError(code="1", description="abc")

                product = await stripe.Product.retrieve_async(company.stripe_subscribe_product_id)

            except InvalidRequestError:
                product = await stripe.Product.create_async(name=f"Subscription for customer")
                await DbCompany(db_id=company.id).update(stripe_subscribe_product_id=product.id)

            amount = 100000
            try:
                if not company.stripe_subscribe_price_id:
                    raise InvalidRequestError(code="1", description="abc")

                price = await stripe.Price.retrieve_async(company.stripe_subscribe_price_id)

            except InvalidRequestError:
                price = await stripe.Price.create_async(
                    product=product.id, unit_amount=100000, currency="pln")
                await DbCompany(db_id=company.id).update(stripe_subscribe_price_id=price.id)

        else:
            return

        try:
            if not company.stripe_customer_id:
                raise InvalidRequestError(code="1", description="abc")

            customer = await stripe.Customer.retrieve_async(company.stripe_customer_id)

        except InvalidRequestError:
            customer = await stripe.Customer.create_async(
                name=f"TG Customer #{uid}", description="Customer from a telegram bot", email="valetinles@gmail.com")
            await DbCompany(tg_user_id=uid).update(stripe_customer_id=customer.id)

        invoice = await stripe.Invoice.create_async(
            customer=customer.id, collection_method="send_invoice", days_until_due=1,
            description="Payment for opening a driver's form."
        )
        # await stripe.InvoiceItem.create_async(customer=customer.id, invoice=invoice.id, price=price.id)
        finalized_invoice = await stripe.Invoice.finalize_invoice_async(invoice=invoice.id)
        invoice_url = finalized_invoice.hosted_invoice_url

        result = await DbPayment(
            creator_id=uid, amount=amount, p_type=db_type, driver_id=current_driver_id, invoice_url=invoice_url,
            status=0, system=PaymentsProcessing.STRIPE, stripe_invoice_id=invoice.id).add()
        if result:
            text = await Ut.get_message_text(lang=company.lang, key="payment_stripe")
            text = text.replace("%reason%", "оплату открытия анкеты водителя")
            text = text.replace("%amount%", str(amount / 100))
            markup = await Cim.payment(invoice_url=invoice_url, lang=company.lang)
            msg = await Ut.send_step_message(user_id=uid, text=text, markup=markup)

            await DbPayment(db_id=result.id).update(msg_to_delete=msg.message_id)

            await state.update_data(system="stripe")
            await state.set_state(CompanyFindDriver.PaymentProcessing)

        else:
            text = await Ut.get_message_text(lang=company.lang, key="payment_create_error")
            await callback.message.answer(text=text)

    @staticmethod
    async def stripe_handling():
        logging.getLogger("aiogram.event").setLevel(logging.WARNING)
        logging.basicConfig(level=logging.INFO,
                            format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

        logger.info(f"Handling stripe payments has started!")
        await connect_to_db(remove_data=False)
        await Ut.load_localizations_files()

        stripe.api_key = Config.STRIPE_SECRET_KEY
        while True:
            await asyncio.sleep(5)

            db_payments = await DbPayment(
                system=PaymentsProcessing.STRIPE, status=0).select(status_with_selected_system=True)
            for payment in db_payments:
                invoice_obj: stripe.Invoice = await stripe.Invoice.retrieve_async(payment.stripe_invoice_id)
                if invoice_obj.status == "paid":
                    await DbPayment(db_id=payment.id).update(status=1)

                    company = await DbCompany(tg_user_id=payment.creator_id).select()
                    if payment.type == PaymentsProcessing.PAY_FOR_DRIVER:
                        driver = await DbDriver(db_id=payment.driver_id).select()
                        company.open_drivers.append(payment.driver_id)
                        if driver.id in company.saved_drivers:
                            company.saved_drivers.remove(driver.id)

                        await DbCompany(db_id=company.id).update(
                            open_drivers=company.open_drivers, saved_drivers=company.saved_drivers)

                        await DbDriver(db_id=driver.id).update(opens_count=driver.opens_count + 1)
                        text = await Ut.get_message_text(lang=company.lang, key="pay_for_driver_success")
                        text = await DriverForm().form_completion(title=text, lang=company.lang, db_model=driver)

                    elif payment.type == PaymentsProcessing.SUBSCRIPTION_FEE:
                        await DbCompany(db_id=company.id).update(paid_subscription=20)
                        text = await Ut.get_message_text(lang=company.lang, key="pay_for_subscription_success")

                    else:
                        return

                    text_payment_success = await Ut.get_message_text(lang=company.lang, key="payment_success")

                    await Config.BOT.delete_message(chat_id=payment.creator_id, message_id=payment.msg_to_delete)
                    await Config.BOT.send_message(chat_id=payment.creator_id, text=text_payment_success)
                    await Config.BOT.send_message(chat_id=payment.creator_id, text=text)

                    if payment.type == PaymentsProcessing.PAY_FOR_DRIVER:
                        text = await Ut.get_message_text(lang=driver.lang, key="msg_to_driver_after_open")
                        await Config.BOT.send_message(chat_id=driver.tg_user_id, text=text)

                elif invoice_obj.status == "open":
                    due_date_dt = datetime.fromtimestamp(invoice_obj.due_date, Config.TIMEZONE)
                    current_dt = datetime.now(tz=Config.TIMEZONE)
                    if current_dt > due_date_dt:
                        await DbPayment(db_id=payment.id).update(status=2)

                        company = await DbCompany(tg_user_id=payment.creator_id).select()
                        text = await Ut.get_message_text(lang=company.lang, key="payment_due_time")

                        await Config.BOT.delete_message(chat_id=payment.creator_id, message_id=payment.msg_to_delete)
                        await Config.BOT.send_message(chat_id=company.tg_user_id, text=text)

    @staticmethod
    async def cryptomus(callback: types.CallbackQuery, state: FSMContext):
        uid = callback.from_user.id

    @staticmethod
    async def cryptomus_handling():
        logging.getLogger("aiogram.event").setLevel(logging.WARNING)
        logging.basicConfig(level=logging.INFO,
                            format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s')

        logger.info(f"Handling cryptomus payments has started!")
        await connect_to_db(remove_data=False)
        await Ut.load_localizations_files()

    @staticmethod
    async def payments_handler(callback: types.CallbackQuery, state: FSMContext):
        await callback.answer()
        uid = callback.from_user.id
        await Ut.handler_log(logger, uid)

        company = await DbCompany(tg_user_id=uid).select()

        data = await state.get_data()
        system = data["system"]
        p_type = data["type"]
        current_driver_id = data.get("current_driver_id")

        cd = callback.data
        if cd == "cancel":
            text = await Ut.get_message_text(lang=company.lang, key="payment_cancel_confirmation")
            markup = await Ut.get_markup(mtype="inline", lang=company.lang, key="confirmation")
            msg = await Ut.send_step_message(user_id=uid, text=text, markup=markup)
            await DbPayment(creator_id=uid, status=0).update(msg_to_delete=msg.message_id)

        elif cd == "back":
            payment: Payment = await DbPayment(creator_id=uid, status=0).select()
            if p_type == "open_driver":
                driver = await DbDriver(db_id=current_driver_id).select()
                text = await Ut.get_message_text(lang=company.lang, key="payment_stripe")
                text = text.replace("%reason%", "оплату открытия анкеты водителя")
                text = text.replace("%amount%", str(int(driver.form_price)))
                markup = await Cim.payment(invoice_url=payment.invoice_url, lang=company.lang)
                msg = await Ut.send_step_message(user_id=uid, text=text, markup=markup)

            elif p_type == "subscribe":
                pass

            else:
                return

            await DbPayment(db_id=payment.id).update(msg_to_delete=msg.message_id)

        elif cd == "confirm":
            payment = await DbPayment(creator_id=uid, status=0).select()
            await DbPayment(db_id=payment.id).update(status=2)

            if system == "stripe":
                await stripe.Invoice.void_invoice_async(payment.stripe_invoice_id)

            elif system == "cryptomus":
                pass

            else:
                return

            text = await Ut.get_message_text(lang=company.lang, key="payment_cancel_complete")
            await Ut.send_step_message(user_id=uid, text=text)
            await asyncio.sleep(1.5)

            await data["function_for_back"](callback=callback, state=state, from_payment_cancel=True)


router.callback_query.register(PaymentsProcessing.payments_handler, CompanyFindDriver.PaymentProcessing)
