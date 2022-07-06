from common import *

class lua_tools:
    module_not_found = re.compile(r"module '(.*?)' not found")
    with open_read('missing_luas.txt', True) as f:
        missing_modules = f.read().split('\n')
    fake_missing_modules = '\n'.join([f'package.loaded["{module}"] = true' for module in missing_modules])
    required_lua = [open_read('resources/Scripts/Config/' + cfg).read() for cfg in ['Excel/CommonScriptConfig.lua', 'Json/ConfigEntity.lua']]
    preamble = '\n'.join(required_lua) + '\n' + fake_missing_modules

    @classmethod
    def format_lua_error(cls, e: lupa.LuaError) -> str:
        s = str(e)
        for module in cls.module_not_found.findall(s):
            return module
        return s.replace('"',"'").replace('\n', ' ')

    @classmethod
    def run(cls, script: str) -> lupa.LuaRuntime:
        lua = lupa.LuaRuntime()
        lua.execute(cls.preamble)
        lua.execute(script)
        return lua

    @classmethod
    def load(cls, script_filename: str) -> lupa.LuaRuntime:
        with open(script_filename, 'r') as file:
            script = file.read()
        lua = lupa.LuaRuntime()
        lua.execute(cls.preamble)
        try:
            lua.execute(script)
        except lupa.LuaError as e:
            lua.globals().errors = {1: cls.format_lua_error(e)}
            if (idx := script.find('\nfunction')) > 0:
                try:
                    lua.execute(script[:idx])
                    line_number = script[:idx].count('\n') + 1
                    lua.globals().errors[2] = f'Succeeded in running up to first function declaration at character {idx} (reached line number {line_number})'
                except lupa.LuaError as e:
                    lua.globals().errors[2] = cls.format_lua_error(e)
        finally:
            return lua


default_lua_globals = set(g for g in lua_tools.run('').globals())
seen_globals = set()
lua_tables = {k:{} for k in ['gadgets', 'groups', 'suites', 'errors']}
lua_full_tables = {}
path = os.path.join(GC_PATH, 'resources/Scripts/Scene/')
for root, dirs, files in os.walk(path):
    for filename in [os.path.join(root, f) for f in files if f.endswith('.lua')]:
        key = filename[len(path):]
        lua = lua_tools.load(filename)
        results = lua.globals()
        wrapped_type = lua.globals().type
        seen_globals |= {key for key in results}
        nondefault_globals = [key for key in results if key not in default_lua_globals]
        nondefaults = {key: results[key] for key in nondefault_globals}
        lua_full_tables[key] = {k: table_to_dict(v) for k,v in nondefaults.items() if wrapped_type(v) != 'function'}
        for name, table in lua_tables.items():
            if (t := results[name]) is not None:
                table[key] = table_to_dict(t)


output_path = 'lua_jsons/'
os.makedirs(output_path, exist_ok=True)
for name, table in lua_tables.items():
    with open_write(output_path + f'luas.scenes.{name}.json', True) as file:
        file.write(encode_json(table))
with open_write(output_path + f'luas.scenes.full_globals.json', True) as file:
    file.write(encode_json(lua_full_tables))
print(f'Total errors: {len(lua_tables["errors"])}')


def _semi_flatten(gadgets):
    if isinstance(gadgets, list):
        return [flatten_json(g, flatten_xyz=True, flatten_lists=False) for g in gadgets]
    elif isinstance(gadgets, dict):
        return flatten_json(gadgets, flatten_xyz=True, flatten_lists=False)
    else:
        return gadgets

def semi_flatten(data, skip_tiers=0):
    if skip_tiers > 0:
        if isinstance(data, list):
            return [semi_flatten(d, skip_tiers-1) for d in data]
        elif isinstance(data, dict):
            return {k:semi_flatten(v, skip_tiers-1) for k,v in data.items()}
        else:
            return data
    if isinstance(data, dict):
        return {key: _semi_flatten(gadgets) for key, gadgets in data.items()}
    elif isinstance(data, list):
        return [_semi_flatten(gadgets) for gadgets in data]
    else:
        return data


for (name, skips) in [(k, 0) for k in lua_tables.keys()] + [('full_globals', 1)]:
    table_decoded = load_json(output_path + f'luas.scenes.{name}.json', True)
    with open_write(output_path + f'flat.luas.scenes.{name}.lua.json', True) as file:
        file.write(encode_json(semi_flatten(table_decoded, skips), maxline=250, sort_overrides={'id': 'AAAid', 'pos': 'AApos'}))

