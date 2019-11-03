import pdb
import sys
import codecs
import datetime

input_paths = sys.argv[1:]

entries = []
for input_path in input_paths:
    print(f"loading wishes from {input_path}")
    with codecs.open(input_path, 'r', encoding='utf-8') as input_file:
        current_entry = None
        for line in input_file:
            if line.startswith('2019'):
                if current_entry is not None:
                    entries.append(current_entry.replace('\n', '<br/>').split('\t'))
                current_entry = line.strip()
            else:
                current_entry += line.strip()

authors = {}
for entry in entries:
    ip = entry[4]
    author = entry[2]
    if ip not in authors:
        authors[ip] = set()
    authors[ip].add(author)

with codecs.open('formatted_wishes.html', 'w', encoding='utf-8') as formatted_file:
    formatted_file.write('<html><body>')
    for entry in sorted(entries, key=lambda e: datetime.datetime.fromisoformat(e[0])):
        timestamp = datetime.datetime.fromisoformat(entry[0])
        print(f"processing wish from {entry[2]}")
        formatted_file.write(f'<p><span style="font-weight: bold">{entry[3]}</span><br/>{entry[1]}<br/><span style="font-style: italic">- {entry[2]} a.k.a. {", ".join([aka for aka in authors[entry[4]] if aka != entry[2]])};</span><span style="color:gray"> {timestamp.time().strftime("%H:%M")}</span></p>')
    formatted_file.write('</body></html>')
