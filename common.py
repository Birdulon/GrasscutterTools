import json
import os
import re
import pandas as pd
import numpy as np
import lupa
from typing import TextIO

INDENT = 2
GC_PATH = '../Grasscutter/'


def open_read(filename: str, local=False) -> TextIO:
    path = '' if local else GC_PATH
    return open(path + filename, 'r')


def open_write(filename: str, local=False) -> TextIO:
    path = '' if local else GC_PATH
    return open(GC_PATH + filename, 'w', encoding='utf-8', newline='\n')


re_handbook = re.compile(r'(\d+) : (.*)')
handbook_items = {}
handbook_others = {}
with open_read('GM Handbook.txt') as f:
    for line in f:
        for key, value in re_handbook.findall(line):
            key = int(key)
            if key not in handbook_items:
                handbook_items[key] = value
            else:
                handbook_others[key] = value


def load_json(filename: str, local=False) -> dict:
    with open_read(filename, local=local) as file:
        return json.load(file)


def save_json(data: dict, filename: str, local=False, indent=INDENT, **kwargs) -> None:
    with open_write(filename, local=local) as file:
        json.dump(data, file, ensure_ascii=False, indent=indent, **kwargs)


def fmt_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    def get_pos(d):
        pos_d = d.get('motion_info', {}).get('pos', {})
        return tuple(pos_d.get(x, 0) for x in 'xyz')
    data = sorted(data, key=get_pos)
    with open(f'{filename.rpartition(".")[0]}.newlines.json', 'w', encoding='utf-8', newline='\n') as f:
        entry_strings = [json.dumps(entry, ensure_ascii=False).replace(' ', '') for entry in data]
        f.write('[\n' + ',\n'.join(entry_strings) + '\n]')


def flatten_json(data: dict, prefix='', flatten_keys=[], flatten_xyz=False, stripped_keys=[], flatten_lists=True) -> dict:
    def squish_xyz(data: dict):
        keys = set(data.keys())
        if len(keys) > 0:
            for xyz in (['x', 'y', 'z'], ['w', 'x', 'y', 'z'], ['propType', 'propValue']):
                if len(keys - set(xyz)) == 0:
                    return tuple(data.get(k, 0) for k in xyz)
        return False
    
    def to_tuple_of_tuples(data):
        if isinstance(data, dict):
            if squish := squish_xyz(data):
                return squish
            return tuple((k, to_tuple_of_tuples(v)) for k,v in data.items())
        elif isinstance(data, list):
            return tuple(to_tuple_of_tuples(v) for v in data)
        else:
            return data

    def flatten(data: dict, prefix=''):
        output = {}
        for key, value in data.items():
            p = prefix + key
            if key in stripped_keys:
                continue
            if isinstance(value, dict):
                if flatten_xyz and (squish := squish_xyz(value)):
                    output[p] = squish
                else:
                    next_prefix = prefix if key in flatten_keys else p+'.'
                    output.update(flatten(value, next_prefix))
            elif isinstance(value, list):
                if flatten_lists:
                    for i,val in enumerate(value):
                        if isinstance(val, dict):
                            output.update(flatten(val, f'{p}.{i}.'))
                        else:
                            output[f'{p}.{i}'] = val
                else:
                    output[p] = to_tuple_of_tuples(value)
            else:
                output[p] = value
        return output

    return flatten(data, prefix)


def unflatten_json(data: dict) -> dict:
    output = {}
    def add_key(key: list, d: dict, value):
        if len(key) == 1:
            d[key[0]] = value
        else:
            d[key[0]] = d.get(key[0], {})
            add_key(key[1:], d[key[0]], value)
    for key, value in data.items():
        add_key(key.split('.'), output, value)
    return output


def load_textmaps():
    path = 'resources/TextMap/'
    textmaps = {}
    for filename in os.listdir(GC_PATH + path):
        if filename.endswith('.json') and filename.startswith('TextMap'):
            key = filename[7:-5]
            if key in ['CHS', 'CHT', 'EN', 'JP', 'RU']:
                textmaps[key] = load_json(path + filename)
    return textmaps


def table_to_dict(lua_table) -> dict:
    if not lua_table:
        return
    if len(lua_table) > 0:  # Only array tables have working length in lupa
        output = []
        for v in lua_table.values():
            if isinstance(v, (int, float, str)):
                output.append(v)
            elif lupa.lua_type(v) == 'table':
                output.append(table_to_dict(v))
    else:
        output = {}
        for k,v in lua_table.items():
            if isinstance(v, (int, float, str)):
                output[k] = v
            elif lupa.lua_type(v) == 'table':
                output[k] = table_to_dict(v)
    return output

