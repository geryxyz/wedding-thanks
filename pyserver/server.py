import time
import datetime
import urllib.request
import urllib.error
import concurrent.futures

from flask import Flask
from flask import request
from flask_api import status

import os
import typing
import codecs
import winsound
import random
import collections

from pyserver.color import Color, red, green, blue, white, black
import pyserver.girl_on_fire
import pyserver.crystal
import pyserver.ice
import pyserver.blue_apple


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


def client_ring(index):
    return clients[index % len(clients)]


@app.route('/reg')
def reg():
    address = request.remote_addr
    if address not in clients:
        clients.append(address)
        with open(reg_backup_file, 'a') as reg_backup:
            reg_backup.write(f'{address}\n')
        print(f"Successful registration: {address} ({clients.index(address)}th client)")
        winsound.Beep(1000, 300)
        winsound.Beep(3000, 100)
        response = get(f'http://{address}/limit?l=0.1')
        print(f'setting limit for {address} to {response}')
    else:
        print(f"Clients already registered. ({clients.index(address)}th client)")
        winsound.Beep(500, 500)
        winsound.Beep(300, 1000)
    return '', status.HTTP_200_OK


def send_toggle():
    print(f"toggling movement on {len(clients)} clients")
    urls = []
    for current in clients:
        url = f'http://{current}/toggle'
        urls.append(url)
    return list(get_all(urls))


def send_show(from_top, from_back, to_top, to_back, duration, current_clients):
    urls = []
    for current in current_clients:
        url = f'http://{current}/show' \
            f'?ftR={from_top.r}&ftG={from_top.g}&ftB={from_top.b}&ttR={to_top.r}&ttG={to_top.g}&ttB={to_top.b}' \
            f'&fbR={from_back.r}&fbG={from_back.g}&fbB={from_back.b}&tbR={to_back.r}&tbG={to_back.g}&tbB={to_back.b}&d={duration}'
        urls.append(url)
    get_all(urls)


ShowEntry = collections.namedtuple('ShowEntry', 'from_top from_back to_top to_back client')


def send_show_per_client(entries: typing.List[ShowEntry], duration: int):
    urls = []
    for current in entries:
        url = f'http://{current.client}/show' \
            f'?ftR={current.from_top.r}&ftG={current.from_top.g}&ftB={current.from_top.b}' \
            f'&ttR={current.to_top.r}&ttG={current.to_top.g}&ttB={current.to_top.b}' \
            f'&fbR={current.from_back.r}&fbG={current.from_back.g}&fbB={current.from_back.b}' \
            f'&tbR={current.to_back.r}&tbG={current.to_back.g}&tbB={current.to_back.b}&d={duration}'
        urls.append(url)
    get_all(urls)


class From(object):
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
        # print(self)
        send_show(self.start[0], self.start[1], self.stop[0], self.stop[1], self.duration, self.clients)


class Display(object):
    def __init__(self):
        self._assignments = {}
        self._start = None
        self._stop = None
        self._client = None
        self._duration = None

    def start(self, top: Color, back: Color):
        self._start = (top, back)
        self._assign()
        return self

    def stop(self, top: Color, back: Color):
        self._stop = (top, back)
        self._assign()
        return self

    def on(self, client: str):
        self._client = client
        self._assign()
        return self

    def _assign(self):
        if self._start is not None and self._stop is not None and self._client is not None:
            self._assignments[self._client] = ShowEntry(
                from_top=self._start[0],
                from_back=self._start[1],
                to_top=self._stop[0],
                to_back=self._stop[1],
                client=self._client
            )
            self._start = None
            self._stop = None
            self._client = None

    def during(self, seconds: float):
        self._duration = int(seconds * 1000)
        return self

    def play(self):
        send_show_per_client(list(self._assignments.values()), self._duration)


class Wait(object):
    def __init__(self, duration: float):
        self.duration = duration

    def __str__(self):
        return f'waiting {self.duration} s'

    def play(self):
        # print(self)
        time.sleep(self.duration)


Playable = typing.Union[From, Wait, Display]


class Animation(object):
    def __init__(self):
        self._steps: typing.List[Playable] = []

    def then(self, step: Playable):
        self._steps.append(step)
        return self

    def continue_with(self, step: From):
        if self._steps:
            if self._steps[-1].clients != step.clients:
                raise ValueError("continuation with different targets")
            step.start = self._steps[-1].stop
        self.then(step)
        return self

    def play(self):
        for step in self._steps:
            step.play()

    def __call__(self, *args, **kwargs):
        self.play()


animations: typing.Dict[str, Animation] = {}


def demo_ani():
    demo_animation = Animation()
    colors = [red, green, blue]
    for color in colors:
        for current in clients:
            demo_animation \
                .then(From(black, black).to(color, color).during(.1).on(current)) \
                .continue_with(From().to(black, black).during(.1).on(current)) \
                .then(Wait(.1))
    demo_animation \
        .then(Wait(.5)) \
        .then(From(black, black).to(white, white).during(1).on(*clients)) \
        .continue_with(From().to(black, black).during(1).on(*clients)) \
        .then(Wait(.5)) \
        .then(Display()
              .start(black, black).stop(red, red).on(clients[0])
              .start(black, black).stop(green, green).on(clients[1])
              .start(black, black).stop(blue, blue).on(clients[2])
              .during(1)) \
        .then(Display()
              .start(red, red).stop(black, black).on(clients[0])
              .start(green, green).stop(black, black).on(clients[1])
              .start(blue, blue).stop(black, black).on(clients[2])
              .during(1))
    return demo_animation


def glow_ani(color: Color):
    return Animation() \
        .then(From(black, black).to(color, color).during(1.5).on(*clients)) \
        .continue_with(From().to(black, black).during(1.5).on(*clients))


def field_ani(colors: typing.List[Color]):
    pass


def init_animations():
    animations['demo'] = demo_ani()
    animations['blessing'] = glow_ani(white)
    animations['peace'] = lambda: glow_ani(random.choice(pyserver.crystal.palette)).play()
    animations['safety'] = lambda: glow_ani(random.choice([
        pyserver.blue_apple.blue_orange,
        pyserver.blue_apple.blue_yellow,
        pyserver.blue_apple.new_stones
    ])).play()


@app.route('/play')
def play():
    selected = request.args.get('animation')
    if selected in animations:
        animations[selected]()
        return f'playing {selected}'
    else:
        return f'missing animation: {selected}'


@app.route('/demo')
def demo():
    animations['demo'].play()
    return 'demo executed'


@app.route('/fast')
def fast():
    animation = Animation()
    colors = [red, green, blue]
    for color in colors * 10:
        for current in clients:
            animation \
                .then(From(black, black).to(color, color).during(.05).on(current)) \
                .continue_with(From().to(black, black).during(.05).on(current))
    animation.play()
    return 'fast test executed'


@app.route('/long')
def long():
    animation = Animation()
    colors = [red, green, blue]
    for color in colors:
        for current in clients:
            animation \
                .then(From(black, black).to(color, color).during(1).on(current)) \
                .continue_with(From().to(black, black).during(1).on(current))
    animation.play()
    return 'long test executed'


last_moved = None
bouncing_limit = 20


@app.route('/move')
def moved():
    global last_moved
    if isinstance(last_moved, float):
        past_time = time.perf_counter() - last_moved
        print(f"{past_time} seconds past since last move")
        if past_time < bouncing_limit:
            print(f"ignoring movement, {bouncing_limit - past_time} seconds left")
            return '', status.HTTP_200_OK
    last_moved = time.perf_counter()
    client = request.remote_addr
    if client in clients:
        print(f"the {clients.index(client)}th client is registered a movement")
        #print(send_toggle())
        animations['demo'].play()
        #print(send_toggle())
        return '', status.HTTP_200_OK
    else:
        return '', status.HTTP_500_INTERNAL_SERVER_ERROR


def serve_file(file_name):
    with codecs.open(file_name, 'r', encoding='utf-8') as page:
        content = page.read()
        return content, status.HTTP_200_OK


@app.route('/wish')
def user_interface():
    return serve_file('wish.html')


@app.route('/exec')
def exec():
    wish = request.args.get('wish')
    name = request.args.get('name')
    if wish is not None and name is not None:
        with codecs.open('wishes.txt', 'a') as wishes:
            wishes.write(f'{datetime.datetime.now()}\t{wish}\t{name}\t{request.remote_addr}\n')
    # TODO: send selected animation
    return serve_file('exec.html')


def load_back_up():
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


def init_clients():
    for current in clients:
        response = ()
        while response != (200, '1'):
            response = get(f'http://{current}/toggle')
            print(f'toggling movement on {current}: {response}')
        response = get(f'http://{current}/limit?l=0.1')
        print(f'setting limit for {current} to {response}')


if __name__ == '__main__':
    load_back_up()
    init_animations()
    init_clients()

    app.run(host='0.0.0.0', port=80, debug=True)
