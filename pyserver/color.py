class Color(object):
    def __init__(self, r, g, b):
        super().__init__()
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return f'#({self.r / 255}-{self.g / 255}-{self.b / 255})'


red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)
black = Color(0, 0, 0)
white = Color(255, 255, 255)
