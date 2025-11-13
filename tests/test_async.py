import asyncio


async def test_async():
    await asyncio.sleep(0.1)
    assert True
