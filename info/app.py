import json

from sanic import Sanic, response

app = Sanic()


@app.route('/api/healthcheck/', methods=['GET'])
async def healthcheck(request):
    return response.json(body={'status': 'OK'})


@app.route('/api/airports/list/', methods=['GET'])
async def get_airports(request):
    with open('helpers/airports.json', 'r') as f:
        airports_data = json.load(f)
        return response.json(airports_data)


@app.route('/api/flights/1/', methods=['GET'])
async def get_flights1(request):
    with open('flights/RS_Via.xml', 'r') as f:
        return response.text(f.read(), content_type='text/xml')


@app.route('/api/flights/2/', methods=['GET'])
async def get_flights2(request):
    with open('flights/RS_ViaOW.xml', 'r') as f:
        return response.text(f.read(), content_type='text/xml')
