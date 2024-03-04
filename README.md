# WIKI-parser

<h3>cache_wiki.py</h3>
A script's called `cache_wiki.py` main purpose will be to download pages
from Wikipedia, but the data we're interested in is links in text and 'See also' sections leading
to other pages inside Wikipedia itself. It only save a graph representation as a JSON file `wiki.json`, 
so that vertices store pages and directed edges are links.

You can shoose any Wikipedia article as a default starting position. Also, code is
able to receive a name of an existing article as an argument to use instead of a default one. 
So, when it is run like this:

`~$ python cache_wiki.py -p 'Erdős number'`

it starts parsing from [this page](https://en.wikipedia.org/wiki/Erd%C5%91s_number).

It keeps following links (only those leading to other Wikipedia pages) going *at least three pages 
deep* down every link. This parameter is configurable using `-d`, so default value will be `3`. But
if the result is too large (>1000 pages) code stops processing links. If it is too small (<20 pages)
then please choose some other default starting page. If page A links to page B and page B links to 
page A - it is two directed graph edges, not one.

Every page your code visits logging to stdout using `logging` Python module with log 
level set to 'INFO'. 

Code also support storing graph in a [Neo4J
database](https://neo4j.com/download/).
<h3>shortest_path.py</h3>
Program called `shortest_path.py` finds the *shortest*
path length between two pages in your serialized database (if these pages are there):

```
~$ python shortest_path.py --from 'Welsh Corgi' --to 'Solomon'
3
~$ python shortest_path.py --from 'Solomon' --to 'Welsh Corgi' --non-directed
3
```
`--non-directed` flag means we treat all links as 'non-directed' or 'bidirected', so
every edge is treated equally in both directions. In this case, a path exists betweeh *any* two
nodes in your serialized graph.

By default (when `--non-directed` is not specified) we are only following the directed edges of 
the graph. This means, not all pages in the database can be reachable from other pages, especially 
if they  have a small amount of inbound links. If the path doesn't exist, script prints
'Path not found'.

The location of the wiki file is reading from the environment variable named `WIKI_FILE`. If
the database file is not found, the code should print 'Database not found'.

Additionally, `-v` flag will enable logging of the found path, like this:

```
~$ python shortest_path.py -v --from 'Welsh Corgi' --to 'Solomon'
'Welsh Corgi' -> 'Dog training' -> 'King Solomon's Ring (book)' -> 'Solomon'
3
```

<h3>render_graph.py</h3>
`render_graph.py` renders a visualization graph of pages (from a file
generated in EX00, also reading it from a `WIKI_FILE` env variable) as a PNG image
`wiki_graph.png`, with nodes and edges.

The size of the node corresponds to the number of incoming 
connections. The more connections - the larger the node in render.

`wiki_graph.html` page will show an interactive visualization of the
graph, and you can save it in png-format.
