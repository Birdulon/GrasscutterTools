from common import *

spawns = load_json('src/main/resources/defaults/data/GadgetSpawns.json')
spawns3 = [spawn for spawn in spawns if spawn['sceneId']==3]
def pos2xy(pos: dict) -> list:  # Rotate to our screenspace
    return [-pos.get("z", 0), pos.get("x", 0)]
def spawns2array(spawns: list) -> np.ndarray:
    # return np.array([pos2xy(s['pos']) for s in spawns if 'pos' in s])
    return [pos2xy(s['pos']) for s in spawns if 'pos' in s]
# centroids = {s['groupId']:pos2xy(s['pos']) for s in spawns3 if 'groupId' in s}
# spawn_points = {s['groupId']:spawns2array(s['spawns']) for s in spawns3 if 'groupId' in s}
# gid_to_centroid_and_points = {s['groupId']:(pos2xy(s['pos']), spawns2array(s['spawns'])) for s in spawns3 if 'groupId' in s}
data = []
gids = []
for s in spawns3:
    if 'groupId' not in s:
        continue
    gid = s['groupId']
    centroid = pos2xy(s['pos'])
    for p in spawns2array(s['spawns']):
        data.append([p, centroid])
        gids.append(gid)
spawn_points = np.array(data)
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
cs = [colors[i%len(colors)] for i in gids]


import matplotlib.pyplot as plt
import matplotlib.collections as mc
plt.rcParams['figure.figsize'] = [60, 50]
# plt.rcParams['figure.dpi'] = 300
plt.axes().set_aspect('equal')
lc = mc.LineCollection(spawn_points, linewidths=2, alpha=0.2, colors=cs)
plt.axes().add_collection(lc, autolim=False)
plt.scatter(spawn_points[:,0,0], spawn_points[:,0,1], c=cs, alpha=0.5)
plt.show()
# plt.savefig('plot.png')
plt.savefig('plot.svg')