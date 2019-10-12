import sys
import pdb
import colourlovers
import re

ids = sys.argv[1:]


def gamma_correction(value):
    # https://learn.adafruit.com/led-tricks-gamma-correction/the-longer-fix
    # pow((float)i / (float)max_in, gamma) * max_out + 0.5)
    return int(255 * (value / 255) ** 2.8 + .5)


def HTMLColorToRGB(colorstring):
    """ convert RRGGBB to an (R, G, B) tuple """
    if len(colorstring) == 6:
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return r, g, b


def simplify(text: str) -> str:
    return re.sub(r'[\W]+', '_', text).lower()


client = colourlovers.ColourLovers()
for id in ids:
    print(f"fetching {int(id)} ... ", end='')
    palette = client.palette(int(id))[0]
    print(palette.title)
    with open(f'{simplify(palette.title)}.py', 'w') as colors:
        colors.write('from pyserver.color import Color\n')
        colors.write(f'# {palette.title} {palette.url}\n')
        for hex in palette.colours:
            print('\tfetching %s ... ' % hex, end='')
            color = client.color(hex)[0]
            print(color.title)
            name = simplify(color.title)
            components = HTMLColorToRGB(hex[1:])
            gamma_components = [gamma_correction(c) for c in components]
            print(f'\t{components} --> {gamma_components}')
            colors.write(f'{name} = Color({", ".join(map(str, gamma_components))})\n')
        colors.write('\n')
