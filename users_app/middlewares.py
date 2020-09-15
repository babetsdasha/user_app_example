from aiohttp import web
from aiohttp.web_exceptions import HTTPException

from users_app.utils import APIException


async def api_exception_middleware(app, handler):
    async def middleware_handler(request):
        try:
            response = await handler(request)
            return response
        except APIException as ex:
            return web.json_response({'return': ex.message,
                                      'code': ex.code, }, status=400)

    return middleware_handler


async def logger_handler(app, handler):
    async def middleware_handler(request):
        if await request.text():
            data = await request.json()
        else:
            data = request.match_info
        try:
            return await handler(request)
        except Exception as error:
            await app['logger'].error(
                '.'.join(['views', handler.__name__]),
                ':'.join([str(type(error)), str(error)]),
                params=data, method=request.method,
                url=request.url
            )
            if isinstance(error, (APIException, HTTPException)):
                raise
            return web.json_response(
                {"error": "Internal server error"},
                status=500
            )

    return middleware_handler
