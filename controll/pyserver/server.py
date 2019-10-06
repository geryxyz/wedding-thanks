import urllib.request
from http.client import HTTPResponse

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


def send_show(index, from_top, from_back, to_top, to_back, duration) -> HTTPResponse:
    url = 'http://'
    url += clients[index]
    url += '/show'
    url += '?ftR={R}&ftG={G}&ftB={B}'.format(**from_top.for_send())
    url += '&ttR={R}&ttG={G}&ttB={B}'.format(**to_top.for_send())
    url += '&fbR={R}&fbG={G}&fbB={B}'.format(**from_back.for_send())
    url += '&tbR={R}&tbG={G}&tbB={B}'.format(**to_back.for_send())
    url += '&d={}'.format(duration)
    return urllib.request.urlopen(url)


@app.route('/demo')
def demo():
    response = send_show(0, Color(255, 0, 0), Color(0, 255, 0), Color(0, 0, 0), Color(0, 0, 0), 1000)
    if response.getcode() == 200:
        return 'Showing demo animation.', status.HTTP_200_OK
    else:
        return 'Something went wrong. Error code: {}'.format(response.getcode()), status.HTTP_500_INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
