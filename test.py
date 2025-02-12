import asyncio

from pydantic import BaseModel


class TestClass:
    a: int = 1
    b: str = "a"
    c: float = 1.2

    @classmethod
    async def test_method(cls):
        print(cls.a)


async def main():
    method = getattr(TestClass, "test_method")
    await method()


if __name__ == "__main__":
    asyncio.run(main())
