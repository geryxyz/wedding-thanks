import time
import urllib.request
import urllib.error
import concurrent.futures

from flask import Flask
from flask import request
from flask_api import status

import os
import typing
import codecs

from pyserver.color import Color, red, green, blue, white, black
import pyserver.girl_on_fire


def get(url) -> typing.Tuple[int, str]:
    with urllib.request.urlopen(url) as response:
        return int(response.getcode()), response.read().decode('utf-8')


def get_all(urls):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return executor.map(get, urls)


app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!', status.HTTP_200_OK


clients = []
reg_backup_file = 'reg.txt'


@app.route('/reg')
def reg():
    address = request.remote_addr
    if address not in clients:
        clients.append(address)
        with open(reg_backup_file, 'a') as reg_backup:
            reg_backup.write(f'{address}\n')
        print(f"Successful registration: {address} ({clients.index(address)}th client)")
    else:
        print(f"Clients already registered. ({clients.index(address)}th client)")
    return '', status.HTTP_200_OK


def send_toggle():
    print(f"toggling movement on {len(clients)} clients")
    urls = []
    for current in clients:
        url = f'http://{current}/toggle'
        urls.append(url)
    return list(get_all(urls))


def send_show(from_top, from_back, to_top, to_back, duration, current_clients):
    print(f"sending show command to {len(current_clients)} clients")
    urls = []
    for current in current_clients:
        url = f'http://{current}/show' \
            f'?ftR={from_top.r}&ftG={from_top.g}&ftB={from_top.b}&ttR={to_top.r}&ttG={to_top.g}&ttB={to_top.b}' \
            f'&fbR={from_back.r}&fbG={from_back.g}&fbB={from_back.b}&tbR={to_back.r}&tbG={to_back.g}&tbB={to_back.b}&d={duration}'
        urls.append(url)
    get_all(urls)


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


def play_demo():
    animation = Animation()
    colors = [red, green, blue]
    for color in colors:
        for current in clients:
            animation\
                .then(Show(black, black).to(color, color).during(.1).on(current))\
                .continue_with(Show().to(black, black).during(.1).on(current))\
                .then(Wait(.1))
    animation\
        .then(Wait(.5))\
        .then(Show(black, black).to(white, white).during(1).on(*clients))\
        .continue_with(Show().to(black, black).during(1).on(*clients))
    animation.play()


@app.route('/demo')
def demo():
    play_demo()
    return 'demo executed'


@app.route('/fast')
def fast():
    animation = Animation()
    colors = [red, green, blue]
    for color in colors * 10:
        for current in clients:
            animation\
                .then(Show(black, black).to(color, color).during(.05).on(current))\
                .continue_with(Show().to(black, black).during(.05).on(current))
    animation.play()
    return 'fast test executed'


@app.route('/long')
def long():
    animation = Animation()
    colors = [red, green, blue]
    for color in colors:
        for current in clients:
            animation\
                .then(Show(black, black).to(color, color).during(1).on(current))\
                .continue_with(Show().to(black, black).during(1).on(current))
    animation.play()
    return 'long test executed'


@app.route('/move')
def moved():
    client = request.remote_addr
    if client in clients:
        print(f"the {clients.index(client)}th client is registered a movement")
        print(send_toggle())
        play_demo()
        print(send_toggle())
        return '', status.HTTP_200_OK
    else:
        return '', status.HTTP_500_INTERNAL_SERVER_ERROR


@app.route('/wish')
def user_interface():
    with codecs.open('wish.html', 'r', encoding='utf-8') as page:
        content = page.read()
        return content, status.HTTP_200_OK


@app.route('/exec')
def exec():
    print(list(request.args.items()))
    return str(list(request.args.items()))


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
                    if int(get(f'http://{client}')[0]) == 200:
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

    for current in clients:
        response = ()
        while response != (200, '1'):
            response = get(f'http://{current}/toggle')
            print(f'toggling movement on {current}: {response}')

    app.run(host='0.0.0.0', port=80, debug=True)
