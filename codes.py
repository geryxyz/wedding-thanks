import re
import glob

code_colors = [
    '000000',
    'FF0000',
    'FFFF00',
    '00FF00',
    '00FFFF',
    '0000FF',
    'FF00FF',
    'FFFFFF'
]

severity_colors = [
    'FFFFFF',
    '00FF00',
    'FFFF00',
    'FF0000'
]


def code_to_span(code):
    return '<span style="background-color:#{0}; padding:0pt 6pt; border:solid black 1pt"></span>'.format(code_colors[code], code)


def severity_to_span(code):
    return '<span style="background-color:#{0}; padding:0pt 2pt; border:solid black 1pt; margin:0pt 1pt"></span>'.format(severity_colors[code], code) * 2


inos = glob.glob('./**/*.ino', recursive=True)

for ino in inos:
    print("scanning {}...".format(ino))
    code_table = {}
    with open(ino, 'r') as code_file:
        in_codes = False
        for line in code_file:
            line = line.strip()
            if line == '//feedbacks table':
                in_codes = True
                continue
            if line == '//end feedbacks table':
                in_codes = False
                continue
            if in_codes and line != '':
                parts = re.split(r'\s+', line)
                name = parts[1]
                codes = [int(e.strip(',')) for e in parts[2:]]
                code_table[name] = codes

    with open(ino + '.html', 'w') as html_file:
        html_file.write('<html><body><table>')
        for name, codes in sorted(code_table.items(), key=lambda e: ''.join(map(str, e[1]))):
            row = ''.join(['<td style="text-align:center">' + code_to_span(e) + '</td>' for e in codes[1:]])
            html_file.write('<tr>')
            html_file.write('<td style="text-align:right">{}</td>'.format(name))
            html_file.write('<td style="text-align:center">{}</td>'.format(severity_to_span(codes[0])))
            html_file.write(row)
            html_file.write('<td style="text-align:center">{}</td>'.format(severity_to_span(codes[0])))
            html_file.write('</tr>')
        html_file.write('</table></html></body>')
