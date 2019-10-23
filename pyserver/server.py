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
import logging

from pyserver.color import Color, red, green, blue, white, black, yellow, cyan, magenta
import pyserver.girl_on_fire
import pyserver.crystal
import pyserver.ice
import pyserver.blue_apple
import pyserver.environment_friendly
import pyserver.stary_night
import pyserver.dutch_seas
import pyserver.dance_to_forget
import pyserver.techno_sailing

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)


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


def set_limit_on(address: str, limit: float=.05):
    response = get(f'http://{address}/limit?l={limit}')
    logger.debug(f'setting limit for {address} to {response}')


@app.route('/reg')
def reg():
    address = request.remote_addr
    if address not in clients:
        clients.append(address)
        with open(reg_backup_file, 'a') as reg_backup:
            reg_backup.write(f'{address}\n')
        logger.info(f"successful registration: {address} ({clients.index(address)}th client)")
        thread = threading.Thread(target=set_limit_on, args=[address])
        thread.start()
        winsound.Beep(1000, 300)
        winsound.Beep(3000, 100)
    else:
        logger.info(f"clients already registered ({clients.index(address)}th client)")
        winsound.Beep(500, 500)
        winsound.Beep(300, 1000)
    return '', status.HTTP_200_OK


def send_toggle():
    logger.info(f"toggling movement on {len(clients)} clients")
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
        logger.debug(self)
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
        logger.debug(self)
        time.sleep(self.duration)


Playable = typing.Union[From, Wait, Display]


class Animation(object):
    def __init__(self):
        self._steps: typing.List[Playable] = []

    def then(self, step: Playable):
        self._steps.append(step)
        return self

    def continue_with(self, step: typing.Union[From, Display]):
        last_step = None
        for candidate_step in self._steps[::-1]:
            if not isinstance(candidate_step, Wait):
                last_step = candidate_step
                break
        if last_step is not None:
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
        logger.debug("playing animation start")
        with animation_lock:
            for step in self._steps:
                step.play()
        logger.debug("playing animation end")

    def reverse(self):
        self._steps = self._steps[::-1]
        return self


animation_lock = threading.Lock()
animations: typing.Dict[str, typing.Callable[[int], Animation]] = {}
local_animations: typing.Dict[str, typing.Callable[[int], Animation]] = {}
global_animations: typing.Dict[str, typing.Callable[[int], Animation]] = {}


def local(animation: typing.Callable[[int], Animation]):
    animation.local = True
    return animation


def is_local(animation: typing.Callable[[int], Animation]):
    return hasattr(animation, 'local') and animation.local


def translate(animation: typing.Callable[[int], Animation], hungarian_name: str):
    animation.hungarian_name = hungarian_name
    return animation


def animations_html_option():
    options = []
    for name, animation in sorted(animations.items(), key=lambda e: e[1].hungarian_name):
        options.append(f'<option value="{name}">{animation.hungarian_name}</option>')
    return '\n'.join(options)


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


def glow_ani(color: Color):
    return Animation() \
        .then(From(black, black).to(color, color).during(1.5).on(*clients)) \
        .continue_with(From().to(black, black).during(1.5).on(*clients))


def field_ani(colors: typing.List[Color], cycle: int, duration: float):
    field_animation = Animation()
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


def spot_ani(forground_colors: typing.List[Color], background_colors: typing.List[Color], spot_chance: float,
             cycle: int, duration: float, spot_background_duration_ratio: float):
    field_animation = Animation()
    if len(clients) > 4:
        duration_per_cycle = duration / (cycle + 2)

        def select():
            if random.random() < spot_chance:
                return random.choice(forground_colors)
            else:
                return random.choice(background_colors)

        field_animation.then(Display()
            .start(black, black).stop(select(), select()).on(clients[0])
            .start(black, black).stop(select(), select()).on(clients[1])
            .start(black, black).stop(select(), select()).on(clients[2])
            .start(black, black).stop(select(), select()).on(clients[3])
            .start(black, black).stop(select(), select()).on(clients[4])
            .during(duration_per_cycle))
        for i in range(cycle):
            field_animation.continue_with(Display()
                .start().stop(select(), select()).on(clients[0])
                .start().stop(select(), select()).on(clients[1])
                .start().stop(select(), select()).on(clients[2])
                .start().stop(select(), select()).on(clients[3])
                .start().stop(select(), select()).on(clients[4])
                .during(duration_per_cycle * spot_background_duration_ratio)) \
            .continue_with(Display()
                .start().stop(random.choice(background_colors), random.choice(background_colors)).on(clients[0])
                .start().stop(random.choice(background_colors), random.choice(background_colors)).on(clients[1])
                .start().stop(random.choice(background_colors), random.choice(background_colors)).on(clients[2])
                .start().stop(random.choice(background_colors), random.choice(background_colors)).on(clients[3])
                .start().stop(random.choice(background_colors), random.choice(background_colors)).on(clients[4])
                .during(duration_per_cycle * (1 - spot_background_duration_ratio)))
        field_animation.continue_with(Display()
            .start().stop(black, black).on(clients[0])
            .start().stop(black, black).on(clients[1])
            .start().stop(black, black).on(clients[2])
            .start().stop(black, black).on(clients[3])
            .start().stop(black, black).on(clients[4])
            .during(duration_per_cycle))
    return field_animation


def round_about(particle_color: Color, trace_color: Color,
                trace_length: int, trace_fadding_factor: float,
                cycle: int, duration: float, offset: int):
    round_about_animation = Animation()
    if len(clients) > 4:
        duration_per_cycle = duration / (cycle + 1)
        for i in range(cycle):
            step = Display().start().stop(particle_color, particle_color).on(clients[ring_index(i + offset)])
            if trace_length > 4:
                raise ValueError("trace max length is 4")
            current_trace_color = trace_color
            for j in range(1, 5):
                if j <= trace_length:
                    step.start().stop(current_trace_color, current_trace_color).on(clients[ring_index(i - j + offset)])
                    current_trace_color = current_trace_color * trace_fadding_factor
                else:
                    step.start().stop(black, black).on(clients[ring_index(i - j + offset)])
            step.during(duration_per_cycle)
            round_about_animation.continue_with(step)
            # round_about_animation.then(Wait(duration_per_cycle * .5))
        round_about_animation.continue_with(Display()
            .start().stop(black, black).on(clients[0])
            .start().stop(black, black).on(clients[1])
            .start().stop(black, black).on(clients[2])
            .start().stop(black, black).on(clients[3])
            .start().stop(black, black).on(clients[4])
            .during(duration_per_cycle))
    return round_about_animation


def ripple(colors: typing.List[Color], duration: float, cycle: int, offset: int):
    def select():
        return random.choice(colors)

    ripple_animation = Animation()
    duration_per_cycle = duration / (4 * cycle)
    for i in range(cycle):
        ripple_animation.continue_with(Display()
            .start().stop(black, black).on(clients[ring_index(-2 + offset)])
            .start().stop(black, black).on(clients[ring_index(-1 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(0 + offset)])
            .start().stop(black, black).on(clients[ring_index(1 + offset)])
            .start().stop(black, black).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))\
        .continue_with(Display()
            .start().stop(black, black).on(clients[ring_index(-2 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(-1 + offset)])
            .start().stop(black, black).on(clients[ring_index(0 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(1 + offset)])
            .start().stop(black, black).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))\
        .continue_with(Display()
            .start().stop(select(), select()).on(clients[ring_index(-2 + offset)])
            .start().stop(black, black).on(clients[ring_index(-1 + offset)])
            .start().stop(black, black).on(clients[ring_index(0 + offset)])
            .start().stop(black, black).on(clients[ring_index(1 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))\
        .continue_with(Display()
            .start().stop(black, black).on(clients[ring_index(-2 + offset)])
            .start().stop(black, black).on(clients[ring_index(-1 + offset)])
            .start().stop(black, black).on(clients[ring_index(0 + offset)])
            .start().stop(black, black).on(clients[ring_index(1 + offset)])
            .start().stop(black, black).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))
    return ripple_animation


def drain(colors: typing.List[Color], duration: float, cycle: int, offset: int):
    def select():
        return random.choice(colors)

    ripple_animation = Animation()
    duration_per_cycle = duration / (4 * cycle)
    for i in range(cycle):
        ripple_animation\
        .continue_with(Display()
            .start().stop(select(), select()).on(clients[ring_index(-2 + offset)])
            .start().stop(black, black).on(clients[ring_index(-1 + offset)])
            .start().stop(black, black).on(clients[ring_index(0 + offset)])
            .start().stop(black, black).on(clients[ring_index(1 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))\
        .continue_with(Display()
            .start().stop(black, black).on(clients[ring_index(-2 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(-1 + offset)])
            .start().stop(black, black).on(clients[ring_index(0 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(1 + offset)])
            .start().stop(black, black).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))\
        .continue_with(Display()
            .start().stop(black, black).on(clients[ring_index(-2 + offset)])
            .start().stop(black, black).on(clients[ring_index(-1 + offset)])
            .start().stop(select(), select()).on(clients[ring_index(0 + offset)])
            .start().stop(black, black).on(clients[ring_index(1 + offset)])
            .start().stop(black, black).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))\
        .continue_with(Display()
            .start().stop(black, black).on(clients[ring_index(-2 + offset)])
            .start().stop(black, black).on(clients[ring_index(-1 + offset)])
            .start().stop(black, black).on(clients[ring_index(0 + offset)])
            .start().stop(black, black).on(clients[ring_index(1 + offset)])
            .start().stop(black, black).on(clients[ring_index(2 + offset)])
            .during(duration_per_cycle))
    return ripple_animation


def init_animations():
    animations['demo'] = translate(lambda offset=random.choice(range(5)): demo_ani(), 'Demo animáció')

    animations['blessing'] = translate(lambda offset=random.choice(range(5)): glow_ani(white), 'Áldás animáció')
    animations['peace'] = translate(lambda offset=random.choice(range(5)): glow_ani(random.choice(pyserver.crystal.palette)), 'Béke animáció')
    animations['safety'] = translate(lambda offset=random.choice(range(5)): glow_ani(random.choice([
        pyserver.blue_apple.blue_orange,
        pyserver.blue_apple.blue_yellow,
        pyserver.blue_apple.new_stones
    ])), 'Biztonság animáció')

    animations['fire'] = translate(lambda offset=random.choice(range(5)): field_ani(
        pyserver.girl_on_fire.palette,
        duration=5, cycle=10), 'Tűz animáció')
    animations['ice'] = translate(lambda offset=random.choice(range(5)): field_ani(
        pyserver.ice.palette,
        duration=5, cycle=10), 'Jég animáció')
    animations['forest'] = translate(lambda offset=random.choice(range(5)): field_ani(
        pyserver.environment_friendly.palette,
        duration=5, cycle=10), 'Zöld erdő animáció')
    animations['happiness'] = translate(lambda offset=random.choice(range(5)): field_ani(
        [red, green, blue, yellow, cyan, magenta],
        duration=5, cycle=10), 'Vidámság animáció')

    animations['comet'] = local(translate(lambda offset=random.choice(range(5)): round_about(
        particle_color=random.choice(pyserver.crystal.palette), trace_color=random.choice(pyserver.ice.palette) * .5,
        trace_length=2, trace_fadding_factor=.3,
        cycle=20, duration=6, offset=offset), 'Üstökös animáció'))

    animations['fireball'] = local(translate(lambda offset=random.choice(range(5)): round_about(
        particle_color=random.choice([
            pyserver.girl_on_fire.orange_peel,
            pyserver.girl_on_fire.bright_ideas
        ]),
        trace_color=random.choice([
            pyserver.girl_on_fire.tomato,
            pyserver.girl_on_fire.red15,
            pyserver.stary_night.plume_stain
        ]) * .5,
        trace_length=3, trace_fadding_factor=.6,
        cycle=30, duration=6, offset=offset), 'Tűzgolyó animáció'))

    animations['nightsky'] = translate(lambda offset=random.choice(range(5)): spot_ani(
        forground_colors=[
            pyserver.stary_night.shitty_blue,
            pyserver.girl_on_fire.bright_ideas,
            pyserver.environment_friendly.doop
        ],
        background_colors=[
            pyserver.stary_night.cobbled_plum,
            pyserver.stary_night.light_fading_,
            pyserver.stary_night.plume_stain,
            pyserver.stary_night.true_eggplant
        ],
        spot_chance=.1, cycle=15,
        duration=10, spot_background_duration_ratio=.33), 'Csillagos ég animáció')

    animations['sparks'] = translate(lambda offset=random.choice(range(5)): spot_ani(
        forground_colors=[
            pyserver.girl_on_fire.orange_peel,
            pyserver.girl_on_fire.bright_ideas,
            pyserver.girl_on_fire.red15
        ],
        background_colors=[
            pyserver.stary_night.cobbled_plum,
            pyserver.stary_night.light_fading_,
            pyserver.stary_night.true_eggplant
        ],
        spot_chance=.1, cycle=15,
        duration=10, spot_background_duration_ratio=.5), 'Szikrák animáció')

    animations['pond'] = local(translate(lambda offset=random.choice(range(5)): ripple(
        colors=pyserver.dutch_seas.palette[1:],
        cycle=random.choice([2, 3, 5]), duration=3, offset=offset), 'Tó animáció'))

    animations['love'] = local(translate(lambda offset=random.choice(range(5)): drain(
        colors=pyserver.dance_to_forget.palette,
        cycle=5, duration=10, offset=offset), 'Szerelem animáció'))

    global local_animations, global_animations
    local_animations = {key: animation for key, animation in animations.items() if is_local(animation)}
    global_animations = {key: animation for key, animation in animations.items() if not is_local(animation)}


@app.route('/play')
def play():
    selected = request.args.get('animation')
    if selected in animations:
        logger.info(f'playing {selected} animation directly triggered from {request.remote_addr}')
        threading.Thread(target=animations[selected]().play).start()
        return f'playing {selected}'
    else:
        return f'missing animation: {selected}'


@app.route('/demo')
def demo():
    animation = request.args.get('animation')
    client = request.args.get('client')
    if animation is not None:
        threading.Thread(target=animations[animation]().play).start()
    if client is not None:
        threading.Thread(target=lambda: Animation()
                         .then(From().to(red, red).on(client))
                         .continue_with(From().to(green, green).on(client).during(1))
                         .continue_with(From().to(blue, blue).on(client).during(1))
                         .continue_with(From().to(black, black).on(client).during(1)).play()).start()
    return serve_file('demo.html')\
        .replace(
            '<a class="animation" href="demo">Demó animáció</a>',
            '\n'.join([f'<a class="animation" href="/demo?animation={key}">{animation.hungarian_name}</a>' for key, animation in animations.items()])
        )\
        .replace(
            '<a class="client" href=""></a>',
            '\n'.join([f'<a class="client" href="/demo?client={client}">{client}</a>' for client in clients])
        ), status.HTTP_200_OK


last_moved = None
bouncing_limit = 20


def moved(selected: str, offset: int):
    logger.debug("moved start")
    try:
        global last_moved
        if isinstance(last_moved, float):
            past_time = time.perf_counter() - last_moved
            logger.debug(f"{past_time} seconds past since last move")
            if past_time < bouncing_limit:
                logger.warning(f"ignoring movement, {bouncing_limit - past_time} seconds left")
                return
        last_moved = time.perf_counter()
        # print(send_toggle())
        logger.info(f"playing {selected} animation triggered by movement on {offset}th client")
        animations[selected](offset=offset).play()
        # print(send_toggle())
    finally:
        logger.debug("moved end")


@app.route('/move')
def move():
    logger.debug("move start")
    try:
        client = request.remote_addr
        if client in clients:
            index = clients.index(client)
            logger.info(f"the {index}th client is registered a movement")
            if random.random() > .25:
                thread = threading.Thread(target=moved, args=[random.choice(list(local_animations.keys())), index])
            else:
                thread = threading.Thread(target=moved, args=[random.choice(list(global_animations.keys())), index])
            thread.start()
            return '', status.HTTP_200_OK
        else:
            return '', status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        logger.debug("move end")


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
    animation = request.args.get('animation')
    if wish is not None and name is not None and animation is not None:
        with codecs.open('wishes.txt', 'a', encoding='utf-8') as wishes:
            wishes.write(f'{datetime.datetime.now()}\t{wish}\t{name}\t{animation}\t{request.remote_addr}\n')
        threading.Thread(target=animations[animation]().play).start()
    wishes_as_html = []
    with codecs.open('wishes.txt', 'r', encoding='utf-8') as wishes:
        for line in wishes:
            parts = line.strip().split('\t')
            wishes_as_html.append(f'<p class="wish">{parts[1]} <span class="animation">{animations[parts[3]].hungarian_name}</span> <span class="name">- {parts[2]} ({parts[-1]})</span></p>')
    return serve_file('exec.html').replace('<p class="wish"></p>', '\n'.join(wishes_as_html)), status.HTTP_200_OK


def load_back_up():
    if os.path.isfile(reg_backup_file):
        logger.info("reloading clients from back-up")
        with open(reg_backup_file, 'r') as reg_backup:
            for index, line in enumerate(reg_backup):
                client = line.strip()
                if client == '':
                    continue
                logger.debug(f"loading #{index} client with IP of {client}")
                try:
                    if int(get(f'http://{client}')[0]) == 200:
                        clients.append(client)
                    else:
                        logger.warning(f"saved client {client} missing, will not loaded next time")
                except urllib.error.URLError:
                    logger.warning(f"saved client {client} missing, will not loaded next time")
        logger.info("clients are loaded from back-up")
    else:
        logger.info("there is not any back-up file present")
    with open(reg_backup_file, 'w') as reg_backup:
        logger.debug(f"re-saving currently aviable {len(clients)} clients")
        reg_backup.write('\n'.join(clients))
        reg_backup.write('\n')


def init_clients():
    for current in clients:
        response = ()
        while response != (200, '1'):
            response = get(f'http://{current}/toggle')
            logger.debug(f'toggling movement on {current}: {response}')
        set_limit_on(current)
    send_show(black, black, white, white, 1000, clients)
    send_show(white, white, black, black, 1000, clients)


@app.before_request
def filter_prefetch():
    logger.debug("before request")


@app.after_request
def debug_after(response):
    logger.debug("after request")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    response.headers['Connection'] = 'close'
    return response


if __name__ == '__main__':
    logger.info('init server and clients')

    load_back_up()
    init_animations()
    init_clients()

    logger.info('starting web server life cycle')
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
