import sys, asyncio
sys.path.insert(0, 'src')
from dependencies import _maybe_get_postgres_session

async def t():
    agen = _maybe_get_postgres_session()
    try:
        val = await agen.__anext__()
        print('session yielded:', val)
    except StopAsyncIteration:
        print('no yield')

asyncio.run(t())
