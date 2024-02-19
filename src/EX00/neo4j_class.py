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

            session.run(
                "MERGE (from:URL {title: $from_title, link: $from_link})",
                from_title=from_title,
                from_link=from_link,
            )

            to_nodes = node.get("to_nodes", [])

            for to_node in to_nodes:
                to_title = to_node.get("title")
                to_link = to_node.get("link")

                session.run(
                    "MERGE (to:URL {title: $to_title, link: $to_link})",
                    to_title=to_title,
                    to_link=to_link,
                )

                session.run(
                    "MATCH (from:URL {title: $from_title}), "
                    "(to:URL {title: $to_title}) "
                    "MERGE (from)-[:CONNECTED]->(to)",
                    from_title=from_title,
                    to_title=to_title,
                )

    def clear_graph(self):
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
