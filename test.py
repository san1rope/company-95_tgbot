import asyncio

import stripe

from config import Config


async def main():
    stripe.api_key = Config.STRIPE_SECRET_KEY

    result = await stripe.Price.modify_async(id="price_1R2qfdGdotDTv7HKhhqW0kEy", active=False)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
