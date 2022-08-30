"""

DISCLAMER: THIS CODE IS NOT WRITEN BY ME. THIS CODE BELONGS TO DEVOXIN.
I WILL CREATE MY OWN CODE FOR THIS AS SOON AS I FIGURE OUT HOW TO DO IT.

"""

import asyncio
import aiohttp
session = aiohttp.ClientSession()

class RequestWrapper:
    __slots__ = ('_req_url', '_req_args', '_req_kwargs')

    def __init__(self, url, *args, **kwargs):
        self._req_url = url
        self._req_args = args
        self._req_kwargs = kwargs

    def __await__(self):
        return self._request().__await__()
        
    def _copy(self, **kwargs):
        return RequestWrapper(self._req_url, *self._req_args, **self._req_kwargs, **kwargs)

    async def _request(self):
        kwargs = self._req_kwargs
        status = kwargs.pop('status', False)
        headers = kwargs.pop('only_headers', False)
        always_return = kwargs.pop('always_return', False)
        json = kwargs.pop('json', False)
        text = kwargs.pop('text', False)
        try:
            async with session.get(self._req_url, *self._req_args, **kwargs) as r:
                if status:
                    return r.status
                if headers:
                    return r.headers
                if r.status != 200 and not always_return:
                    return None
                if json:
                    return await r.json(content_type=None)
                body = await r.read()
                if text:
                    return body.decode(errors='ignore')
                return body
        except (aiohttp.ClientOSError, aiohttp.ClientConnectorError, asyncio.TimeoutError):
            return None

    def status(self):
        return self._copy(status=True)

    def headers(self):
        return self._copy(only_headers=True)

    def always_return(self):
        return self._copy(always_return=True)

    def json(self):
        return self._copy(json=True)

    def text(self):
        return self._copy(text=True)


def status(url, *args, **kwargs) -> RequestWrapper:
    return RequestWrapper(url, *args, **kwargs).status()


def get(url, *args, **kwargs) -> RequestWrapper:
    return RequestWrapper(url, *args, **kwargs)


async def post(url, always_return=False, json=False, *args, **kwargs):
    try:
        async with session.post(url, *args, **kwargs) as r:
            if r.status != 200 and not always_return:
                return None
            if json:
                return await r.json(content_type=None)
            return await r.read()
    except (aiohttp.ClientOSError, aiohttp.ClientConnectorError, asyncio.TimeoutError):
        return None


def get_headers(url, *args, **kwargs) -> RequestWrapper:
    return get(url, *args, **kwargs).headers()