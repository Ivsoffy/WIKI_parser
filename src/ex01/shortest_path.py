import argparse
import json


def dikstra(dict_js: dict, fr: str, to: str):
    dict_d = dict_js.copy()
    for d in dict_d.keys():
        dict_d[d] = {"visited": 0, "distance": float('inf'), "prev": 0}

    dict_d[fr]["distance"] = 0
    dict_d[fr]["prev"] = 0

    node = 0
    n_count = 0
    while node != to:
        node = min_dist(dict_d)
        n_count += 1
        if n_count > len(dict_js):
            return -1
        dict_d[node]["visited"] = 1
        for i in dict_js[node]:
            if i in dict_js.keys() and dict_d[i]["distance"] > dict_d[node]["distance"] + 1:
                dict_d[i]["distance"] = dict_d[node]["distance"] + 1
                dict_d[i]["prev"] = node
    way = [to]
    w = to
    while w != fr:
        way.append(dict_d[w]["prev"])
        w = dict_d[w]["prev"]
    way.reverse()
    return {"distance": dict_d[to]["distance"], "way": way}


def min_dist(dict_d: dict) -> str:
    min_dist_node = None
    k = float('inf')
    for i in dict_d.keys():
        if dict_d[i]["visited"] == 0 and dict_d[i]["distance"] < k:
            k = dict_d[i]["distance"]
            min_dist_node = i
    return min_dist_node

 
parser = argparse.ArgumentParser()
# parser.add_argument("--fr", "--from",  required=True)
# parser.add_argument("--to", required=True)
# parser.add_argument("--non-directed", action="store_true")
# parser.add_argument("-v", action="store_true")
args = parser.parse_args()
args.fr = "node1"
args.to = "node8"
args.v = True
args.non_directed = False

with open('WIKI_FILE.json', 'r') as wiki_file:
    wiki_js = json.load(wiki_file)

if args.non_directed:
    for i in wiki_js.keys():
        for j in wiki_js[i]:
            if j not in wiki_js.keys():
                wiki_js[j] = [i]
            else:
                if i not in wiki_js[j]:
                    wiki_js[j].append(i)

res = dikstra(wiki_js, args.fr, args.to)

if res != -1:
    if args.v:
        for i, n in enumerate(res["way"]):
            if i != len(res["way"]) - 1:
                print('\'' + n + '\'', end=' -> ')
            else:
                print('\'' + n + '\'')
    print(res["distance"])
else:
    print("Database not found")

