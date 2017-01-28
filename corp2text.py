import re
import os
from collections import defaultdict
import numpy as np
import json

def get_content(file):
    '''
    Removes headers from file
    '''

    with open(file) as f:
        text = [l.strip('\n') for l in f.readlines()]

    line = text[0]
    while not "/author" in line:
        text.pop(0)
        line = text[0]
    text.pop(0)
    return text

def parse(text):
    '''
    Removes tags from text
    '''
    r = re.compile('([^\/]*)')
    p = ''
    for line in text:
        m = r.match(line)
        if m:
            p += " %s" % m.group(0)
    quote = (l.strip() for l in p.split("''") if l)
    out = []
    for l in quote:
        lines = filter(bool,l.split('.'))
        dotted = ["%s.\n" % s.strip() for s in lines[:-1] if s]
        if lines:
            dotted.append("%s\"\n" % lines[-1].strip())
        out += dotted

    return out

def get_names(text):
    r = re.compile('(?<!^)(?<!`` )(?<!\? )(?<!\! )(?<!\, )[A-Z][a-z]+')
    names = defaultdict(int)
    for line in text:
        for name in r.findall(line):
            names[name] += 1
    avg = np.mean(names.values())
    for key in names.keys():
        if names[key] < avg*2 or key=='The':
            del names[key]
    return names.keys()

def replace_names(text):
    new = []
    ids = {}
    i=0
    for name in get_names(text):
        ids[name] = i
        i+=1

    for line in text:
        for name in ids.keys():
            line = re.sub(name, 'person_%d' % ids[name], line)

        line = re.sub('person_(\d) (person_\d)+',r"person_\1",line)
        new.append(line)
    return new

def concat(dir,use_json=False):
    unique = set()
    r = re.compile('^[^c].*\.txt$')
    full = []
    for path, subdirs, files in os.walk(dir):
        for f in files:
            if r.match(f) and f not in unique:
                t = get_content("%s/%s" % (path, f))
                p = parse(t)
                p = replace_names(p)
                full += p
                unique.add(f)
    if use_json:
        with open('input.json','w') as f:
           json.dump(full, f) 
    with open('input.txt','w') as f:
        f.writelines(full)

def name_main(dir):
    t = get_content(dir)
    p = parse(t)
    return get_names(p)

if __name__ == '__main__':
   concat('corpus-map') 
