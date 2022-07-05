from common import *

def test_inheritance(data: dict, root_key='gadget.gadgetId') -> dict:
    data_flat = [flatten_json(d) for d in data]
    by_root_key = {}
    for d in data_flat:
        key = d.get(root_key, 0)
        l = by_root_key.get(key, [])
        l.append(d)
        by_root_key[key] = l
    len(by_root_key)

    output = {}
    for id, gs in by_root_key.items():
        template = {k:v for k,v in gs[0].items() if k != root_key}
        children = []
        for child in gs[1:]:
            c = {}
            for k,v in child.items():
                if k == root_key:
                    continue
                if k not in template or template[k] != v:
                    c[k] = v
            children.append(c)
        if len(children):
            template['zz_children'] = children
        output[id] = template
    return output

def get_best_parents(data_flat):
    def remaining_props(d, parent) -> int:
        r = len(d)
        for k,v in d.items():
            if k in parent and parent[k] == v:
                r -= 1
        return r

    best_parents = {}
    total = len(data_flat)
    for i in range(total-1):
        print(f'Finding best parent {i+1}/{total-1}')
        d = data_flat[-(i+1)]
        uid = d['_UID']
        min_r = len(d)
        best_parent_uid = -1
        for j in range(total-i-1):
            parent = data_flat[j]
            if parent['_UID'] == uid:
                continue
            r = remaining_props(d, parent)
            if r < min_r:
                min_r = r
                best_parent_uid = parent['_UID']
        best_parents[uid] = best_parent_uid
    return best_parents

def test_bruteforce_inheritance(data_flat, best_parents) -> list:
    def inherit(d, parent, parent_full) -> dict:
        child = {}
        for k,v in d.items():
            if k == '_UID':
                continue
            if not (k in parent_full and parent_full[k] == v):
                child[k] = v
        child = unflatten_json(child)
        children = parent.get('zz_children', [])
        children.append(child)
        parent['zz_children'] = children
        return child
    
    output = []
    lookups = {}
    full_parents = {d['_UID']:d for d in data_flat}
    for d in data_flat:
        uid = d['_UID']
        bp = best_parents.get(uid, -1)
        if bp > -1 and bp in lookups:
            lookups[uid] = inherit(d, lookups[bp], full_parents[bp])
        else:
            d2 = {k:v for k,v in d.items() if k!='_UID'}
            d2 = unflatten_json(d2)
            output.append(d2)
            lookups[uid] = d2
    return output

# def turn_progenitors_into_groups(data):
#     if isinstance(data, list):
#         for item in list:
#             turn_progenitors_into_groups(item)
#     elif isinstance(data, dict):
#         if 'zz_children' not in data:
#             return

data = load_json('3.json')
data_flat_unsorted = [flatten_json(d, flatten_keys=['gadget', 'motionInfo'], flatten_xyz=True, stripped_keys=['entityId']) for d in data]
data_flat = sorted(data_flat_unsorted, key=lambda x: (len(x), x.get('gadget.gadgetId', 0)))

# for i, d in enumerate(data_flat):
#     d['_UID'] = i
# best_parents = get_best_parents(data_flat)
# df4 = test_bruteforce_inheritance(data_flat, best_parents)
#save_json(df4, '3.flatdense.json')

# s = json.dumps(df4, ensure_ascii=False)
# s2 = s.replace('},', '},\n')
# s3 = s2.replace(' ', '').replace('"zz_children"', '\n"zz"').replace('configId', 'c').replace('groupId', 'g')
# with open_write('3.flatdense.json', True) as f:
#     f.write(s3)

# o = turn_progenitors_into_groups(load_json('3.df4.json'))

def format_dump(input) -> str:
    MAX_LINE = 130
    def format_d(data, indent=0) -> list:
        prefix = '\t' * indent
        if isinstance(data, dict):
            s = json.dumps(data)  # str(data)
            if len(s) < MAX_LINE:  # Inline
                return [prefix+s]
            else:  # Expand all elements
                output = [prefix+'{']
                prefix2 = prefix+'\t'
                for k,v in data.items():
                    if k == 'zz_children':
                        output.append(f'{prefix2}"children": [')
                        for value in v:
                            output += format_d(value, indent+2)
                            output[-1] = output[-1] + ','
                        output.append(f'{prefix2}],')
                    else:
                        s = json.dumps(v)  # str(v)
                        if len(s) < MAX_LINE:
                            output.append(f'{prefix2}"{k}": {s},')
                        else:
                            output.append(f'{prefix2}"{k}":')
                            output += format_d(v, indent+1)
                output.append(prefix+'},')
                return output
        elif isinstance(data, list):
            s = json.dumps(data)  # str(data)
            if len(s) < MAX_LINE:  # Inline
                return [prefix+s]
            else:  # Expand all elements
                output = [prefix+'[']
                for value in data:
                    output += format_d(value, indent+1)
                output.append(prefix+'],')
                return output
        else:
            return [prefix + str(data)]
    return '\n'.join(format_d(input))
# with open_write('3.flatdense2.json', True) as f:
    # f.write(format_dump(df4))


data = load_json('3.json')
data_flat = sorted([flatten_json(
        d, flatten_keys=['gadget', 'motionInfo', 'gatherGadget'], flatten_xyz=True, flatten_lists=False) for d in data],
        key=lambda x: (len(x), x.get('gadgetId', 0)))
df = pd.DataFrame(data_flat)
df1 = df.loc[:,df.nunique(dropna=False)!=1].sort_values(['itemId', 'groupId', 'entityId', 'configId', 'gadgetId'])
# df1[df1.nunique().sort_values().index].to_excel('3.xlsx')
# gatherable_counts = df['gatherGadget.itemId'].value_counts()
# {handbook_items.get(int(x), int(x)):y for x,y in gatherable_counts.sort_values().iteritems()}

def make_gatherable_templates(df: pd.DataFrame):
    def make_template(df, name):
        common_values = df.loc[:, df.nunique(dropna=False) == 1]
        varying_values = df.loc[:, df.nunique(dropna=False) > 1]
        output = {'TemplateName': name}
        for k,v in common_values.iloc[0].iteritems():
            output[k] = v
        output['zChildren'] = varying_values.to_dict('records')
        return output

    gatherable_counts = df['itemId'].value_counts()
    one_ofs = gatherable_counts[gatherable_counts == 1].index
    multiple_ofs = gatherable_counts[gatherable_counts > 1].index
    outputs = []
    for gatherable_id in multiple_ofs:
        name = handbook_items.get(int(gatherable_id), gatherable_id)
        outputs.append(make_template(df[df['itemId'] == gatherable_id], name))
    outputs.append(make_template(df[df['itemId'].isin(one_ofs)], 'one_ofs'))
    outputs.append(make_template(df[df['itemId'].isnull()], 'NaNs'))
    return outputs
