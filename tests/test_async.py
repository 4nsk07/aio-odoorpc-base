import pytest
from aio_odoorpc_base.aio.common import login
from aio_odoorpc_base.aio.object import execute_kw
from aio_odoorpc_base.protocols import T_AsyncHttpClient
import httpx
import aiohttp
import asyncio


@pytest.mark.asyncio
async def test_async_httpx1(url_db_user_pwd: list, aio_benchmark):
    url, db, user, pwd = url_db_user_pwd
    async with httpx.AsyncClient(base_url=url) as session:
        aio_benchmark(async_login_search_read, '', db, user, pwd, session)


@pytest.mark.asyncio
async def test_async_httpx2(url_db_user_pwd: list, aio_benchmark):
    url, db, user, pwd = url_db_user_pwd
    async with httpx.AsyncClient() as session:
        aio_benchmark(async_login_search_read, url, db, user, pwd, session)
        

@pytest.mark.asyncio
async def test_async_aiohttp(url_db_user_pwd: list, aio_benchmark):
    url, db, user, pwd = url_db_user_pwd
    async with aiohttp.ClientSession() as session:
        await async_login_search_read(url, db, user, pwd, session)


async def async_login_search_read(url: str, db: str, user: str, pwd: str, session: T_AsyncHttpClient):
    uid = await login(session, url, db=db, login=user, password=pwd)
    limit = 10
    fields = ['partner_id', 'date_order', 'amount_total']
    exkw_kwargs = {'http_client': session,
                   'url': url,
                   'db': db,
                   'uid': uid,
                   'password': pwd,
                   'obj': 'sale.order',
                   'method': 'search_read',
                   'args': [],
                   'kw': {'fields': fields}}
    
    data1 = asyncio.create_task(execute_kw(**exkw_kwargs))
    
    exkw_kwargs['method'] = 'search_count'
    exkw_kwargs['kw'] = None
    count = asyncio.create_task(execute_kw(**exkw_kwargs))
    
    exkw_kwargs['method'] = 'search'
    ids = asyncio.create_task(execute_kw(**exkw_kwargs))

    ids = await ids
    exkw_kwargs['method'] = 'read'
    exkw_kwargs['args'] = ids
    exkw_kwargs['kw'] = {'fields': fields}
    data2 = asyncio.create_task(execute_kw(**exkw_kwargs))
    
    count = await count
    data1 = await data1
    data2 = await data2
    
    assert len(data1) == count
    assert len(ids) == count
    assert len(data2) == count
    
    if 'id' not in fields:
        fields.append('id')
    
    for f in fields:
        for d in data1:
            assert d.get(f)
    
    for f in fields:
        for d in data2:
            assert d.get(f)
    
    ids1 = [d.get('id') for d in data1]
    ids2 = [d.get('id') for d in data2]
    ids.sort()
    ids1.sort()
    ids2.sort()
    
    assert len(ids) == len(ids1) and len(ids) == len(ids2)
    
    data1 = {d.get('id'): d for d in data1}
    data2 = {d.get('id'): d for d in data2}
    
    for i in range(0, len(ids) - 1):
        assert ids[i] == ids1[i] == ids2[i]
        
        for f in fields:
            assert data1[ids[i]][f] == data2[ids[i]][f]
