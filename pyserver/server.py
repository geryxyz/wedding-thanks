import time
import datetime
import urllib.request
import urllib.error
import concurrent.futures
import threading

from flask import Flask
from flask import request
from flask_api import status

import os
import typing
import codecs
import winsound
import random
import collections

from pyserver.color import Color, red, green, blue, white, black, yellow, cyan
import pyserver.girl_on_fire
import pyserver.crystal
import pyserver.ice
import pyserver.blue_apple
import pyserver.environment_friendly


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


def ring_index(index) -> int:
    return index % len(clients)


def set_limit_on(address: str, limit: float=.1):
    response = get(f'http://{address}/limit?l={limit}')
    print(f'setting limit for {address} to {response}')


@app.route('/reg')
def reg():
    address = request.remote_addr
    if address not in clients:
        clients.append(address)
        with open(reg_backup_file, 'a') as reg_backup:
            reg_backup.write(f'{address}\n')
        print(f"Successful registration: {address} ({clients.index(address)}th client)")
        thread = threading.Thread(target=set_limit_on, args=[address])
        thread.start()
        winsound.Beep(1000, 300)
        winsound.Beep(3000, 100)
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
        self._assignments: typing.Dict[str, ShowEntry] = {}
        self._start = None
        self._stop = None
        self._client = None
        self._duration = None

    def start(self, top: Color = black, back: Color = black):
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
    def __init__(self, hungarian_name='Névtelen animáció'):
        self._steps: typing.List[Playable] = []
        self.hungarian_name = hungarian_name

    def then(self, step: Playable):
        self._steps.append(step)
        return self

    def continue_with(self, step: typing.Union[From, Display]):
        if self._steps:
            last_step = self._steps[-1]
            if isinstance(step, From) and isinstance(last_step, From):
                if last_step.clients != step.clients:
                    raise ValueError("continuation with different targets")
                step.start = last_step.stop
            elif isinstance(step, Display) and isinstance(last_step, Display):
                for client, last_assignment in last_step._assignments.items():
                    if client in step._assignments:
                        current_assignment = step._assignments[client]
                        step._assignments[client] = ShowEntry(
                            last_assignment.to_top, last_assignment.to_back,
                            current_assignment.to_top, current_assignment.to_back,
                            client)
                    else:
                        raise ValueError("continuation with different targets")
        self.then(step)
        return self

    def play(self):
        for step in self._steps:
            step.play()

    def __call__(self, *args, **kwargs):
        return self


animations: typing.Dict[str, Animation] = {}


def animations_html_option():
    options = []
    for name, animation in animations.items():
        options.append(f'<option value="{name}">{animation().hungarian_name}</option>')
    return '\n'.join(options)


def demo_ani():
    demo_animation = Animation(hungarian_name='Demo animáció')
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
        .then(Wait(.5))
    if len(clients) > 4:
        demo_animation.then(Display()
              .start(black, black).stop(red, red).on(clients[0])
              .start(black, black).stop(yellow, yellow).on(clients[1])
              .start(black, black).stop(green, green).on(clients[2])
              .start(black, black).stop(cyan, cyan).on(clients[3])
              .start(black, black).stop(blue, blue).on(clients[4])
              .during(1))
        for i in range(10):
            demo_animation.continue_with(Display()
                  .start().stop(red, red).on(clients[ring_index(i)])
                  .start().stop(yellow, yellow).on(clients[ring_index(i + 1)])
                  .start().stop(green, green).on(clients[ring_index(i + 2)])
                  .start().stop(cyan, cyan).on(clients[ring_index(i + 3)])
                  .start().stop(blue, blue).on(clients[ring_index(i + 4)])
                  .during(1))
        demo_animation.continue_with(Display()
             .start().stop(black, black).on(clients[0])
             .start().stop(black, black).on(clients[1])
             .start().stop(black, black).on(clients[2])
             .start().stop(black, black).on(clients[3])
             .start().stop(black, black).on(clients[4])
             .during(1))
    return demo_animation


def glow_ani(color: Color, hungarian_name):
    return Animation(hungarian_name=hungarian_name) \
        .then(From(black, black).to(color, color).during(1.5).on(*clients)) \
        .continue_with(From().to(black, black).during(1.5).on(*clients))


def field_ani(colors: typing.List[Color], cycle: int, duration: float, hungarian_name: str):
    field_animation = Animation(hungarian_name=hungarian_name)
    if len(clients) > 4:
        duration_per_cycle = duration / (cycle + 2)
        field_animation.then(Display()
            .start(black, black).stop(random.choice(colors), random.choice(colors)).on(clients[0])
            .start(black, black).stop(random.choice(colors), random.choice(colors)).on(clients[1])
            .start(black, black).stop(random.choice(colors), random.choice(colors)).on(clients[2])
            .start(black, black).stop(random.choice(colors), random.choice(colors)).on(clients[3])
            .start(black, black).stop(random.choice(colors), random.choice(colors)).on(clients[4])
            .during(duration_per_cycle))
        for i in range(cycle):
            field_animation.continue_with(Display()
                .start().stop(random.choice(colors), random.choice(colors)).on(clients[0])
                .start().stop(random.choice(colors), random.choice(colors)).on(clients[1])
                .start().stop(random.choice(colors), random.choice(colors)).on(clients[2])
                .start().stop(random.choice(colors), random.choice(colors)).on(clients[3])
                .start().stop(random.choice(colors), random.choice(colors)).on(clients[4])
                .during(duration_per_cycle))
        field_animation.continue_with(Display()
            .start().stop(black, black).on(clients[0])
            .start().stop(black, black).on(clients[1])
            .start().stop(black, black).on(clients[2])
            .start().stop(black, black).on(clients[3])
            .start().stop(black, black).on(clients[4])
            .during(duration_per_cycle))
    return field_animation


def init_animations():
    animations['demo'] = demo_ani
    animations['blessing'] = lambda: glow_ani(white, 'Áldás animáció')
    animations['peace'] = lambda: glow_ani(random.choice(pyserver.crystal.palette), 'Béke animáció')
    animations['safety'] = lambda: glow_ani(random.choice([
        pyserver.blue_apple.blue_orange,
        pyserver.blue_apple.blue_yellow,
        pyserver.blue_apple.new_stones
    ]), 'Biztonság animáció')
    animations['fire'] = lambda: field_ani(pyserver.girl_on_fire.palette, duration=5, cycle=10, hungarian_name='Tűz animáció')
    animations['ice'] = lambda: field_ani(pyserver.ice.palette, duration=5, cycle=10, hungarian_name='Jég animáció')
    animations['forest'] = lambda: field_ani(pyserver.environment_friendly.palette, duration=5, cycle=10, hungarian_name='Zöld erdő animáció')


@app.route('/play')
def play():
    selected = request.args.get('animation')
    if selected in animations:
        animations[selected]().play()
        return f'playing {selected}'
    else:
        return f'missing animation: {selected}'


@app.route('/demo')
def demo():
    animations['demo']().play()
    return 'demo executed'


last_moved = None
bouncing_limit = 20


def moved():
    global last_moved
    if isinstance(last_moved, float):
        past_time = time.perf_counter() - last_moved
        print(f"{past_time} seconds past since last move")
        if past_time < bouncing_limit:
            print(f"ignoring movement, {bouncing_limit - past_time} seconds left")
            return
    last_moved = time.perf_counter()
    # print(send_toggle())
    print(f"playing animation")
    animations['demo']().play()
    # print(send_toggle())


@app.route('/move')
def move():
    client = request.remote_addr
    if client in clients:
        print(f"the {clients.index(client)}th client is registered a movement")
        thread = threading.Thread(target=moved)
        thread.start()
        return '', status.HTTP_200_OK
    else:
        return '', status.HTTP_500_INTERNAL_SERVER_ERROR


def serve_file(file_name) -> str:
    with codecs.open(file_name, 'r', encoding='utf-8') as page:
        content = page.read()
        return content


@app.route('/wish')
def user_interface():
    return serve_file('wish.html').replace('<option value="demo">Demo animáció</option>', animations_html_option()), status.HTTP_200_OK


@app.route('/exec')
def exec():
    wish = request.args.get('wish')
    name = request.args.get('name')
    if wish is not None and name is not None:
        with codecs.open('wishes.txt', 'a') as wishes:
            wishes.write(f'{datetime.datetime.now()}\t{wish}\t{name}\t{request.remote_addr}\n')
    # TODO: send selected animation
    return serve_file('exec.html'), status.HTTP_200_OK


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
        set_limit_on(current)


if __name__ == '__main__':
    load_back_up()
    init_animations()
    init_clients()

    app.run(host='0.0.0.0', port=80, debug=True)
