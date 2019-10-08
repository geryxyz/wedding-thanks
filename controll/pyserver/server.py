import time
import urllib.request
import concurrent.futures

from flask import Flask
from flask import request
from flask_api import status


def get(url):
    with urllib.request.urlopen(url) as response:
        result = response
    return result


def get_all_sync(urls):
    responses = [get(url) for url in urls]
    return all([int(response.getcode()) == 200 for response in responses])


def get_all(urls):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        responses = executor.map(get, urls)
        return all([int(response.getcode()) == 200 for response in responses])


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
        print(f"Successful registration: {client} ({clients.index(client)}th client)")
    else:
        print(f"Clients already registered. ({clients.index(client)}th client)")
    return '', status.HTTP_200_OK


class Color(object):
    def __init__(self, r, g, b):
        super().__init__()
        self.r = r
        self.g = g
        self.b = b


def send_show(from_top, from_back, to_top, to_back, duration, current_clients):
    urls = []
    for client in current_clients:
        url = f'http://{client}/show' \
            f'?ftR={from_top.r}&ftG={from_top.g}&ftB={from_top.b}&ttR={to_top.r}&ttG={to_top.g}&ttB={to_top.b}' \
            f'&fbR={from_back.r}&fbG={from_back.g}&fbB={from_back.b}&tbR={to_back.r}&tbG={to_back.g}&tbB={to_back.b}&d={duration}'
        print(url)
        urls.append(url)
    get_all(urls)


red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)
black = Color(0, 0, 0)


@app.route('/demo')
def demo():
    for client in clients:
        send_show(black, black, red, red, 1000, [client])
        send_show(red, red, black, black, 1000, [client])
    time.sleep(1)
    send_show(black, black, red, red, 1000, clients)
    send_show(red, red, black, black, 1000, clients)
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
