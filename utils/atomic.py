from functools import wraps

from aiojobs.aiohttp import spawn

def atomic_w_app(coro):
    @wraps(coro)
    async def wrapper(request, **kwargs):
        job = await spawn(request, coro(request, **kwargs))
        return await job.wait()
    return wrapper
