import time
import urllib.request
import concurrent.futures

from flask import Flask
from flask import request
from flask_api import status

import os


def get(url):
    with urllib.request.urlopen(url) as response:
        result = response
    return result


def get_all_sync(urls):
    responses = [get(url) for url in urls]
    return all([int(response.getcode()) == 200 for response in responses])


def get_all(urls):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        start = time.perf_counter()
        responses = executor.map(get, urls)
        print(f"took {time.perf_counter() - start} secs to send")
        return all([int(response.getcode()) == 200 for response in responses])


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!', status.HTTP_200_OK


clients = []
reg_backup_file = 'reg.txt'

@app.route('/reg')
def reg():
    client = request.remote_addr
    if client not in clients:
        clients.append(client)
        with open(reg_backup_file, 'a') as reg_backup:
            reg_backup.write(f'{client}\n')
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

    def __str__(self):
        return f'color({self.r / 255},{self.g / 255},{self.b / 255})'


def send_show(from_top, from_back, to_top, to_back, duration, current_clients):
    print(f"sending show command to {len(current_clients)} clients")
    urls = []
    for client in current_clients:
        url = f'http://{client}/show' \
            f'?ftR={from_top.r}&ftG={from_top.g}&ftB={from_top.b}&ttR={to_top.r}&ttG={to_top.g}&ttB={to_top.b}' \
            f'&fbR={from_back.r}&fbG={from_back.g}&fbB={from_back.b}&tbR={to_back.r}&tbG={to_back.g}&tbB={to_back.b}&d={duration}'
        urls.append(url)
        print(f"{from_top}|{from_back} --> {to_top}|{to_back}")
    get_all(urls)


red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)
black = Color(0, 0, 0)


@app.route('/demo')
def demo():
    colors = [red, green, blue]
    for color in colors:
        for client in clients:
            send_show(black, black, color, color, 500, [client])
            send_show(color, color, black, black, 500, [client])
            time.sleep(.01)
    time.sleep(.5)
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
    if os.path.isfile(reg_backup_file):
        print("reloading clients from back-up")
        with open(reg_backup_file, 'r') as reg_backup:
            for index, line in enumerate(reg_backup):
                client = line.strip()
                print(f"#{index}: {client}")
                if int(get(f'http://{client}').getcode()) == 200:
                    clients.append(client)
                else:
                    print(f"saved client {client} missing")
    else:
        print("there is not any back-up file present")
    with open(reg_backup_file, 'w') as reg_backup:
        print("saving currently registered clients")
        reg_backup.write('\n'.join(clients))
        reg_backup.write('\n')
    app.run(host='0.0.0.0', port=80, debug=True)
