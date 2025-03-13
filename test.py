import asyncio

import stripe


async def main():
    api_key = "sk_test_51QkNgeGdotDTv7HK9xGz5DcuanBmjWZjDGlNSzVH7gSEA23R9s88KnDCNEL0XQFYRBfKuzwJEeydr2DtGhRJuUlq00tDshvYQV"
    stripe.api_key = api_key

    product = stripe.Product.create(name="Toy")
    price = stripe.Price.create(product=product.id, unit_amount=1000, currency="pln")
    customer = stripe.Customer.create(name="Maxim Lored", email="valetinles@gmail.com", description="Test customer")
    invoice = stripe.Invoice.create(
        customer=customer.id, collection_method="send_invoice", days_until_due=1, description="Invoice for driver"
    )
    finalized_invoice = stripe.Invoice.finalize_invoice(invoice=invoice.id)
    invoice_url = finalized_invoice.hosted_invoice_url

    print(f"invoice_url = {invoice_url}")


if __name__ == "__main__":
    asyncio.run(main())
