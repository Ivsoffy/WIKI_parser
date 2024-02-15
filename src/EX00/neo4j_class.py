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
                "MERGE (n:URL {title: $title, link: $link}) RETURN n",
                title=from_title,
                link=from_link,
            )

            for to_node in node.get("to_nodes", []):
                to_title = to_node.get("title")
                to_link = to_node.get("link")

                session.run(
                    "MERGE (n:URL {title: $title, link: $link}) RETURN n",
                    title=to_title,
                    link=to_link,
                )

                session.run(
                    "MATCH (from:URL {title: $from_title, link: $from_link}), "
                    "(to:URL {title: $to_title, link: $to_link}) "
                    "MERGE (from)-[:CONNECTED]->(to)",
                    from_title=from_title,
                    from_link=from_link,
                    to_title=to_title,
                    to_link=to_link,
                )

    def clear_graph(self):
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
