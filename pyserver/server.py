import time
import urllib.request
import urllib.error
import concurrent.futures

from flask import Flask
from flask import request
from flask_api import status

import os
import typing


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
        return f'#({self.r / 255}-{self.g / 255}-{self.b / 255})'


def send_show(from_top, from_back, to_top, to_back, duration, current_clients):
    print(f"sending show command to {len(current_clients)} clients")
    urls = []
    for current in current_clients:
        url = f'http://{current}/show' \
            f'?ftR={from_top.r}&ftG={from_top.g}&ftB={from_top.b}&ttR={to_top.r}&ttG={to_top.g}&ttB={to_top.b}' \
            f'&fbR={from_back.r}&fbG={from_back.g}&fbB={from_back.b}&tbR={to_back.r}&tbG={to_back.g}&tbB={to_back.b}&d={duration}'
        urls.append(url)
    get_all(urls)


red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)
black = Color(0, 0, 0)
white = Color(255, 255, 255)


class Show(object):
    def __init__(self, front: Color = black, back: Color = black):
        self.start = (front, back)
        self.stop = (black, black)
        self.duration = 1000
        self.clients = []

    def to(self, front: Color, back: Color):
        self.stop = (front, back)
        return self

    def during(self, seconds: float):
        self.duration = int(seconds * 1000)
        return self

    def on(self, *target: str):
        self.clients = target
        return self

    def __str__(self):
        return f'{" | ".join(map(str, self.start))} [ {self.duration / 1000} s ] {" | ".join(map(str, self.stop))} on {" , ".join(self.clients)}'

    def play(self):
        # TODO: send it to clients
        print(self)
        send_show(self.start[0], self.start[1], self.stop[0], self.stop[1], self.duration, self.clients)


class Wait(object):
    def __init__(self, duration: float):
        self.duration = duration

    def __str__(self):
        return f'waiting {self.duration} s'

    def play(self):
        print(self)
        time.sleep(self.duration)


Playable = typing.Union[Show, Wait]


class Animation(object):
    def __init__(self):
        self._steps: typing.List[Playable] = []

    def then(self, step: Playable):
        self._steps.append(step)
        return self

    def continue_with(self, step: Show):
        if self._steps:
            if self._steps[-1].clients != step.clients:
                raise ValueError("continuation with different targets")
            step.start = self._steps[-1].stop
        self.then(step)
        return self

    def play(self):
        for step in self._steps:
            step.play()


@app.route('/demo')
def demo():
    animation = Animation()
    colors = [red, green, blue]
    for color in colors:
        for client in clients:
            animation\
                .then(Show(black, black).to(color, color).during(.1).on(client))\
                .continue_with(Show().to(black, black).during(.1).on(client))\
                .then(Wait(.1))
    animation\
        .then(Wait(.5))\
        .then(Show(black, black).to(white, white).during(1).on(*clients))\
        .continue_with(Show().to(black, black).during(1).on(*clients))
    animation.play()
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
                if client == '':
                    continue
                print(f"#{index}: {client}")
                try:
                    if int(get(f'http://{client}').getcode()) == 200:
                        clients.append(client)
                    else:
                        print(f"saved client {client} missing")
                except urllib.error.URLError:
                    print(f"saved client {client} missing")
    else:
        print("there is not any back-up file present")
    with open(reg_backup_file, 'w') as reg_backup:
        print("saving currently registered clients")
        reg_backup.write('\n'.join(clients))
        reg_backup.write('\n')
    app.run(host='0.0.0.0', port=80, debug=True)
