class Color(object):
    def __init__(self, r, g, b):
        super().__init__()
        self.r = r
        self.g = g
        self.b = b

    def __str__(self):
        return f'#({self.r / 255}-{self.g / 255}-{self.b / 255})'

    def __mul__(self, other: float):
        return Color(
            int(self.r * other),
            int(self.g * other),
            int(self.b * other))


red = Color(255, 0, 0)
green = Color(0, 255, 0)
blue = Color(0, 0, 255)

yellow = Color(255, 255, 0)
cyan = Color(0, 255, 255)
magenta = Color(255, 0, 255)

black = Color(0, 0, 0)
white = Color(255, 255, 255)
