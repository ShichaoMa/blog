import asyncio


class A:

    def __init__(self):
        self.a = 1
        self.lock = asyncio.Lock()

    async def run(self):
        async with self.lock:
            self.a += 1
            await asyncio.sleep(1)
            self.a -= 1
            print(self.a)


a = A()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.gather(a.run(), a.run(), a.run(), a.run()))