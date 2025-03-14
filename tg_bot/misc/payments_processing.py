import logging
from typing import Optional

import stripe
from aiogram import types
from aiogram.fsm.context import FSMContext

from config import Config
from tg_bot.db_models.quick_commands import DbDriver, DbPayment

logger = logging.getLogger(__name__)


class PaymentsProcessing:

    @staticmethod
    async def stripe(callback: types.CallbackQuery, state: FSMContext):
        uid = callback.from_user.id

        data = await state.get_data()
        current_driver_id = data["current_driver"]

        driver = await DbDriver(tg_user_id=current_driver_id).select()

        stripe.api_key = Config.STRIPE_SECRET_KEY
        product = stripe.Product.create(name=f"Driver's form #{current_driver_id}")
        price = stripe.Price.create(product=product.id, unit_amount=driver.form_price * 100, currency="pln")
        customer = stripe.Customer.create(name=f"TG Customer #{uid}", description="Customer from a telegram bot")
        invoice = stripe.Invoice.create(
            customer=customer.id, collection_method="send_invoice", days_until_due=1,
            description="Payment for opening a driver's form."
        )
        stripe.InvoiceItem.create(customer=customer.id, invoice=invoice.id, price=price.id)
        finalized_invoice = stripe.Invoice.finalize_invoice(invoice=invoice.id)
        invoice_url = finalized_invoice.hosted_invoice_url

        result = await DbPayment(
            creator_id=uid, amount=driver.form_price, p_type="pay_for_driver", driver_id=current_driver_id,
            invoice_url=invoice_url, status=0
        ).add()

    @staticmethod
    async def cryptomus(callback: types.CallbackQuery, state: FSMContext):
        uid = callback.from_user.id
