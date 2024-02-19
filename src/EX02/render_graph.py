import json
import networkx as nx
from bokeh.plotting import figure, from_networkx, show
from bokeh.models import BoxZoomTool, Circle, HoverTool, MultiLine, ResetTool
from bokeh.palettes import Spectral4
import os
from dotenv import load_dotenv


EDGE_COLOR = "navy"
NODE_COLOR = Spectral4[0]


def count_incoming_nodes(wiki_js):
    edges = []
    incoming_connects = {}
    for i in wiki_js:
        for j in i["to_nodes"]:
            edges.append((i["from_node"]["title"], j["title"]))
            if j["title"] in incoming_connects.keys():
                incoming_connects[j["title"]] += 1
            else:
                incoming_connects[j["title"]] = 1
    return edges, incoming_connects


def print_graph(wiki_js):
    edges, incoming_connects = count_incoming_nodes(wiki_js)
    nodes = incoming_connects.keys()
    titles = []
    for i in incoming_connects.keys():
        titles.append(i)
    node_attr = dict()

    # initialize graph
    g = nx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edges)
    mapping = dict((n, i) for i, n in enumerate(g.nodes))
    g = nx.relabel_nodes(g, mapping)

    # set sizes for nodes
    for node in g.nodes():
        node_size = 10 + incoming_connects[titles[node]] * 3
        node_attr[node] = node_size
        if node == len(titles)-1:
            break
    nx.set_node_attributes(g, node_attr, "node_size")

    # create graph
    graph = from_networkx(g, nx.kamada_kawai_layout, scale=1, center=(0, 0))  # kamada_kawai_layout or spring_layout

    # set up graph
    p = figure(title="WIKI", x_range=(-1.1, 1.1), y_range=(-1.1, 1.1))
    graph.node_renderer.glyph = Circle(size="node_size", fill_color=NODE_COLOR)
    graph.edge_renderer.glyph = MultiLine(line_color=EDGE_COLOR, line_alpha=0.8, line_width=1)
    graph.node_renderer.data_source.data['title'] = titles
    node_hover_tool = HoverTool(tooltips=[("index", "@index"), ("title", "@title")])
    p.add_tools(node_hover_tool, BoxZoomTool(), ResetTool())
    p.renderers.append(graph)
    show(p)


def main():
    load_dotenv(dotenv_path=os.getcwd() + '/.env')
    with open(os.environ.get('WIKI_FILE'), 'r') as wiki:
        wiki_js = json.load(wiki)

    print_graph(wiki_js)


if __name__ == "__main__":
    main()
