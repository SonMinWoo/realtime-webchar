import aiohttp
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.http_websocket import WSCloseCode, WSMessage
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple, Union
import jinja2
import aiohttp_jinja2
import random
import aioredis
import os

REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')

here = Path(__file__).resolve().parent

async def redis_conn(key):
    if(str(type(key)) == "<class 'str'>"):
        redis = aioredis.from_url("redis://localhost")
        key = 'cookie'+key
        value = await redis.get(key)
        if value == None:
            await redis.set(key, "visited")
            return "new"
        else:
            return "visited"
        redis.close()

async def index_handler(request: Request) -> web.Response:
    context = {}
    response = aiohttp_jinja2.render_template("index.html", request, context=context)
    
    return response


async def broadcast(app: web.Application, message: dict) -> None:
    for x in app['websockets'].items():
        print(x)
    for ws in app['websockets'].items():
        await ws[1].send_json(message)

async def change_nick(
    app: web.Application, new_nick: str, old_nick: str, password: str
) -> Tuple[Dict[str, Union[str, bool]], bool]:

    redis = aioredis.from_url("redis://{}".format(REDIS_HOST))
    value = await redis.get(new_nick)
    if value == None:
        await redis.set(new_nick, password)
    else:
        return (
            {'action': 'set_nick', 'success': False, 'message': 'Name already in use.'},
            False,
        )

    if new_nick in app['websockets'].keys():
        return (
            {'action': 'set_nick', 'success': False, 'message': 'Name already in use.'},
            False,
        )
    else:
        app['websockets'][new_nick] = app['websockets'].pop(old_nick)
        return {'action': 'set_nick', 'success': True, 'message': ''}, True

async def ws_chat(request: Request) -> web.WebSocketResponse:
    current_websocket = web.WebSocketResponse(autoping=True, heartbeat=60) 
    ready = current_websocket.can_prepare(request=request)
    if not ready:
        await current_websocket.close(code=WSCloseCode.PROTOCOL_ERROR)
    await current_websocket.prepare(request)


    user = f'User{random.randint(0, 999999)}'
    


    await current_websocket.send_json({'action': 'connecting', 'user': user})

    if request.app['websockets'].get(user):
        await current_websocket.close(code=WSCloseCode.TRY_AGAIN_LATER, message=b'Username already in use')
        return current_websocket
    else:
        request.app['websockets'][user] = current_websocket
        for ws in request.app['websockets'].values():
            await ws.send_json({'action': 'join', 'user': user})
    try:
        async for message in current_websocket:  
            if isinstance(message, WSMessage):
                if message.type == web.WSMsgType.text:  
                    message_json = message.json()
                    action = message_json.get('action')
                    if action not in ['set_nickname', 'new_message', 'user_list']:
                        await current_websocket.send_json(
                            {'action': action, 'success': False, 'message': 'Not allowed.'}
                        )

                    if action == 'set_nickname':
                        new_nickname = message_json.get('nick')[0]
                        password = message_json.get('nick')[1]
                        return_body, success = await change_nick(
                            app=request.app, new_nick=new_nickname, old_nick=user, password=password
                        )
                        if not success:
                            await current_websocket.send_json(return_body)
                        else:
                            await current_websocket.send_json(return_body)
                            await broadcast(
                                app=request.app,
                                message={
                                    'action': 'change_nick',
                                    'from_user': user,
                                    'to_user': new_nickname,
                                },
                            )  
                            user = new_nickname

                    elif action == 'user_list':
                        user_list =  {'action': 'user_list', 'success': True, 'users': list(app['websockets'].keys())}
                        nowuser = message_json.get('cookie')
                        await current_websocket.send_json(user_list)

                    elif action == 'new_message':
                        await broadcast(
                            app=request.app,
                            message={'action': 'new_message', 'message': message_json.get('message'), 'user': user},
                        )

    finally:
        request.app['websockets'].pop(user)

    await broadcast(
        app=request.app, message={'action': 'left', 'user': user}
    )

    return current_websocket


app = web.Application()
aiohttp_jinja2.setup(
    app, loader=jinja2.FileSystemLoader(here)
)
app['websockets'] = defaultdict(dict)
app.router.add_static('/prefix',str(here)+'/public', show_index=True)
app.router.add_get('/', index_handler)
app.router.add_get('/chat', handler=ws_chat)


if __name__ == '__main__':
    web.run_app(app)


