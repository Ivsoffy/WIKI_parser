import argparse
import json
import os


def dikstra(dict_js: list, from_node: str, to_node: str, non_directed: bool):
    dict_d = {}
    for d in dict_js:
        dict_d[d["from_node"]["title"]] = {
            "to_nodes": [],
            "visited": 0,
            "distance": 0 if d["from_node"]["title"] == from_node else float('inf'),
            "prev": "None"
        }
        for n in d["to_nodes"]:
            dict_d[d["from_node"]["title"]]['to_nodes'].append(n["title"])

    if non_directed:
        dict_d = non_directed_expansion(dict_d, from_node, to_node)

    n_count = 0
    while True:
        node = min_dist(dict_d)
        n_count += 1
        if n_count > len(dict_d):
            return -1
        dict_d[node]["visited"] = 1
        for n in dict_d[node]["to_nodes"]:
            if n == to_node:
                way_list = way([to_node, node], dict_d, from_node, node)
                return {"distance": dict_d[node]["distance"] + 1, "way": way_list}
            if n in dict_d.keys() and dict_d[n]["distance"] > dict_d[node]["distance"] + 1:
                dict_d[n]["distance"] = dict_d[node]["distance"] + 1
                dict_d[n]["prev"] = node


def non_directed_expansion(dict_d: dict, from_node: str, to_node: str):
    dict_dop = {}
    for i in dict_d.keys():
        for j in dict_d[i]["to_nodes"]:
            if j not in dict_d.keys():
                if j not in dict_dop.keys():
                    dict_dop[j] = {
                        "to_nodes": [i],
                        "visited": 0,
                        "distance": 0 if j == from_node else float('inf'),
                        "prev": "None"
                    }
                else:
                    dict_dop[j]["to_nodes"].append(i)
            else:
                if i not in dict_d[j]["to_nodes"]:
                    dict_d[j]["to_nodes"].append(i)
    dict_d.update(dict_dop)

    dict_d_copy = dict_d.copy()
    for d in dict_d_copy.keys():
        if len(dict_d[d]["to_nodes"]) == 1 and d != from_node:
            del dict_d[d]
    del dict_d_copy
    return dict_d


def way(way_list: list, dict_d: dict, from_node: str, to_node: str):
    w = to_node
    while w != from_node:
        way_list.append(dict_d[w]["prev"])
        w = dict_d[w]["prev"]
    way_list.reverse()
    return way_list


def min_dist(dict_d: dict) -> str:
    min_dist_node = None
    k = float('inf')
    for d in dict_d.keys():
        node = dict_d[d]
        if node["visited"] == 0 and node["distance"] < k:
            k = node["distance"]
            min_dist_node = d
    return min_dist_node


def main():
    # os.environ['WIKI_FILE'] = '../EX00/graph.json'

    parser = argparse.ArgumentParser()
    parser.add_argument("--fr", "--from",  required=True)
    parser.add_argument("--to", required=True)
    parser.add_argument("--non-directed", action="store_true")
    parser.add_argument("-v", action="store_true")
    args = parser.parse_args()

    with open(os.environ.get('WIKI_FILE'), 'r') as wiki_file:
        wiki_js = json.load(wiki_file)

    res = dikstra(wiki_js, args.fr, args.to, args.non_directed)

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


if __name__ == "__main__":
    main()
