def async_partial(f, *args):
    async def f2(*args2):
        return await f(*args, *args2)
    return f2
