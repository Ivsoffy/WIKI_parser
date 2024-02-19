import json
import networkx as nx
from bokeh.plotting import figure, from_networkx, show
from bokeh.models import BoxZoomTool, Circle, HoverTool, MultiLine, ResetTool
from bokeh.palettes import Spectral4

incoming_connects = {}
edges = []

# with open(os.environ.get('WIKI_FILE'), 'r') as wiki:
with open('graph.json', 'r') as wiki:
    wiki_js = json.load(wiki)

for i in wiki_js:
    for j in i["to_nodes"]:
        edges.append((i["from_node"]["title"], j["title"]))
        if j["title"] in incoming_connects.keys():
            incoming_connects[j["title"]] += 1
        else:
            incoming_connects[j["title"]] = 1

# print(incoming_connects.values())
nodes = incoming_connects.keys()
# d = incoming_connects.values()

# newG = zip(range(len(nodes)), nodes)
COLOR = "navy"
edge_attr = dict()
G = nx.Graph()
G.add_nodes_from(nodes)
G.add_edges_from(edges)
mapping = dict((n, i) for i, n in enumerate(G.nodes))
H = nx.relabel_nodes(G, mapping)

for start_node, end_node in G.edges():
    edge_attr[(start_node, end_node)] = COLOR
nx.set_edge_attributes(G, edge_attr, "edge_color")

p = figure(title="WIKI", x_range=(-1.1,1.1), y_range=(-1.1,1.1))
# p.renderers.append(graph)
l = []

for i in incoming_connects.keys():
    l.append(i)


graph = from_networkx(H, nx.spring_layout, scale=1, center=(0,0))
graph.node_renderer.data_source.data['index'] = list(range(len(G)))
graph.node_renderer.data_source.data['title'] = l
graph.node_renderer.glyph = Circle(size=15, fill_color=Spectral4[0])
# graph.edge_renderer.glyph = MultiLine(line_color = "edge_color", line_alpha = 0.7, line_width =1)

node_hover_tool = HoverTool(tooltips=[("index", "@index"), ("title", "@title")])
p.add_tools(node_hover_tool, BoxZoomTool(), ResetTool())
p.renderers.append(graph)
show(p)
