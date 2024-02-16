from neo4j import GraphDatabase


class Neo4jDriver:
    def __init__(self, uri, username, password):
        self._driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self._driver.close()

    def create_graph(self, node):

        with self._driver.session() as session:
            from_node = node.get("from_node", {})
            from_title = from_node.get("title")
            from_link = from_node.get("link")

            to_nodes = node.get("to_nodes", [])

            query = """
            MERGE (from:URL {title: $from_title, link: $from_link})
            WITH from
            UNWIND $to_nodes AS to_data
            MERGE (to:URL {title: to_data.title, link: to_data.link})
            MERGE (from)-[:CONNECTED]->(to)
            RETURN from, to
            """

            params = {
                "from_title": from_title,
                "from_link": from_link,
                "to_nodes": to_nodes,
            }

            session.run(query, params)

    def clear_graph(self):
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
