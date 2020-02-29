import aiohttp
from exceptions import WrongIncomeData
from sanic import Sanic, response
from sanic_openapi import swagger_blueprint
from urls import setup_routes

app = Sanic()
app.blueprint(swagger_blueprint)
setup_routes(app)


# Server Hooks
@app.listener('before_server_start')
def init(app, loop):
    app.session = aiohttp.ClientSession(loop=loop)


@app.listener('after_server_stop')
def finish(app, loop):
    loop.run_until_complete(app.session.close())
    loop.close()


# Exceptions Handlers
@app.exception(WrongIncomeData)
async def wrong_data_handler(request, exception):
    return response.json({'error': 'Provide both source and destination'}, status=400)
