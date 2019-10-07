import aiohttp
from http.client import HTTPResponse
import asyncio

from flask import Flask
from flask import request
from flask_api import status

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!', status.HTTP_200_OK


clients = []


@app.route('/reg')
def reg():
    client = request.remote_addr
    if client not in clients:
        clients.append(client)
        print("Successful registration: {} ({}th client)".format(client, len(clients)))
        return '', status.HTTP_200_OK
    else:
        return '', status.HTTP_500_INTERNAL_SERVER_ERROR


class Color(object):
    def __init__(self, r, g, b):
        super().__init__()
        self.r = r
        self.g = g
        self.b = b

    def for_send(self):
        return {'R': self.r, 'G': self.g, 'B': self.b}


async def fetch(session, url):
    with aiohttp.Timeout(10):
        async with session.get(url) as response:
            return await response.text()


async def fetch_all(session, urls):
    results = await asyncio.gather(
        *[fetch(session, url) for url in urls],
        return_exceptions=True
    )

    for idx, url in enumerate(urls):
        print('{}: {}'.format(url, 'ERR' if isinstance(results[idx], Exception) else 'OK'))
    return results


def send_show(from_top, from_back, to_top, to_back, duration, current_clients):
    urls = []
    for client in current_clients:
        url = 'http://'
        url += client
        url += '/show'
        url += '?ftR={R}&ftG={G}&ftB={B}'.format(**from_top.for_send())
        url += '&ttR={R}&ttG={G}&ttB={B}'.format(**to_top.for_send())
        url += '&fbR={R}&fbG={G}&fbB={B}'.format(**from_back.for_send())
        url += '&tbR={R}&tbG={G}&tbB={B}'.format(**to_back.for_send())
        url += '&d={}'.format(duration)
        print(url)
        urls.append(url)

    loop = asyncio.get_event_loop()
    with aiohttp.ClientSession(loop=loop) as session:
        results = loop.run_until_complete(fetch_all(session, urls))
        print(results)
    #loop.close()


red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)
black = Color(0, 0, 0)


@app.route('/demo')
def demo():
    for client in clients:
        send_show(black, black, red, red, 100, [client])
        send_show(red, red, black, black, 100, [client])
    return "demo executed"


@app.route('/move')
def moved():
    client = request.remote_addr
    if client in clients:
        return '', status.HTTP_200_OK
    else:
        return '', status.HTTP_500_INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
