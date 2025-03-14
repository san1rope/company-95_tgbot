import asyncio

import stripe

from config import Config


async def main():
    stripe.api_key = Config.STRIPE_SECRET_KEY

    product = stripe.Product.create(name="s")
    price = stripe.Price.create(product=product.id, unit_amount=1000, currency="pln")
    customer = stripe.Customer.create(name="Abraham Sobaka", description="Customer from telegram bot")
    invoice = stripe.Invoice.create(
        customer=customer.id, collection_method="send_invoice", days_until_due=1,
        description="Invoice for driver"
    )

    stripe.InvoiceItem.create(customer=customer.id, price=price.id, invoice=invoice.id)

    finalized_invoice = stripe.Invoice.finalize_invoice(invoice=invoice.id)
    invoice_url = finalized_invoice.hosted_invoice_url

    print(f"invoice_url = {invoice_url}")


if __name__ == "__main__":
    asyncio.run(main())
