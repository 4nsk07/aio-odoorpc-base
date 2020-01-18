import pytest
import asyncio
from aio_odoorpc_base.helpers import odoo_base_url2jsonrpc_endpoint
from bs4 import BeautifulSoup
import httpx
import requests
import aiohttp


@pytest.fixture(scope='package')
def url_db_user_pwd():
    with httpx.Client() as client:
        resp = client.get(url='http://runbot.odoo.com/runbot')
    
    soup = BeautifulSoup(resp.text, features='html.parser')
    tags = soup.find_all("td", class_="bg-success-light")

    urls = []
    
    for tag in tags:
        try:
            url = tag.div.div.find('a', title='Sign in on this build')['href']
            url_parts = url.split('?db=')
            if len(url_parts) == 2:
                json_url = odoo_base_url2jsonrpc_endpoint(url_parts[0])
                return [json_url, url_parts[1], 'demo', 'demo']
        except:
            pass

    return None


@pytest.yield_fixture(scope='package')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
    
    
@pytest.yield_fixture(scope='function')
def aio_benchmark(benchmark):
    import asyncio
    import threading
    
    class Sync2Async:
        def __init__(self, coro, *args, **kwargs):
            self.coro = coro
            self.args = args
            self.kwargs = kwargs
            self.custom_loop = None
            self.thread = None
        
        def start_background_loop(self) -> None:
            asyncio.set_event_loop(self.custom_loop)
            self.custom_loop.run_forever()
        
        def __call__(self):
            evloop = None
            awaitable = self.coro(*self.args, **self.kwargs)
            # breakpoint()
            try:
                evloop = asyncio.get_running_loop()
            except:
                pass
            if evloop is None:
                return asyncio.run(awaitable)
            else:
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=1) as executor:
                    evloop.run_in_executor(executor, self.coro, *self.args)
                
                return
                if not self.custom_loop or not self.thread or not self.thread.is_alive():
                    self.custom_loop = asyncio.new_event_loop()
                    self.thread = threading.Thread(target=self.start_background_loop, daemon=True)
                    self.thread.start()
                
                return asyncio.run_coroutine_threadsafe(awaitable, self.custom_loop).result()
    
    def _wrapper(func, *args, **kwargs):
        if asyncio.iscoroutinefunction(func):
            benchmark(Sync2Async(func, *args, **kwargs))
        else:
            benchmark(func, *args, **kwargs)

    return _wrapper
