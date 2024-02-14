from neo4j import GraphDatabase


def create_nodes_and_edges(tx, nodes):
    index = 1
    for url1, url2 in nodes:
        print(index)
        index += 1
        # url1, url2 = node_pair
        result1 = tx.run(
            "OPTIONAL MATCH (n:URL {url: $url}) RETURN n", url=url1
        )
        result2 = tx.run(
            "OPTIONAL MATCH (n:URL {url: $url}) RETURN n", url=url2
        )

        if not result1.single():
            tx.run("MERGE (n:URL {url: $url}) RETURN n", url=url1)
        if not result2.single():
            tx.run("MERGE (n:URL {url: $url}) RETURN n", url=url2)

        tx.run(
            "MATCH (u1:URL {url: $url1}), (u2:URL {url: $url2}) CREATE (u1)-[:CONNECTED]->(u2)",
            url1=url1,
            url2=url2,
        )
        # tx.run(
        #     """
        #     MERGE (u1:URL {url: $url1})
        #     MERGE (u2:URL {url: $url2})
        #     MERGE (u1)-[:CONNECTED]->(u2)
        #     """,
        #     url1=url1,
        #     url2=url2,
        # )


class Neo4jDriver:
    def __init__(self, uri, username, password):
        self._driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self._driver.close()

    def check_node_exists(self, url):
        with self._driver.session() as session:
            result = session.run(
                "MATCH (n:URL {url: $url}) RETURN COUNT(n) > 0 AS nodeExists",
                url=url,
            )
            return result.single()["nodeExists"]

    def add_node(self, url):
        with self._driver.session() as session:
            if not self.check_node_exists(url):
                session.run("MERGE (n1:URL {url: $url}) RETURN n1", url=url)

    def create_graph(self, set_of_nodes):
        with self._driver.session() as session:
            index = 1
            for url1, url2 in set_of_nodes:
                print(index)
                index += 1

                # if not self.check_node_exists(url1):
                #     session.run(
                #         "MERGE (n1:URL {url: $url1}) RETURN n1", url1=url1
                #     )

                # if not self.check_node_exists(url2):
                #     session.run(
                #         "MERGE (n2:URL {url: $url2}) RETURN n2", url2=url2
                #     )

                # session.run(
                #     "MERGE (n1:URL {url: $url1}) RETURN n1 "
                #     "MERGE (n2:URL {url: $url2}) RETURN n2 "
                #     "MATCH (u1:URL {url: $url1}), (u2:URL {url: $url2}) "
                #     "CREATE (u1)-[:CONNECTED]->(u2)",
                #     url1=url1,
                #     url2=url2,
                # )
                session.run(
                    "MERGE (n1:URL {url: $url1}) "
                    "MERGE (n2:URL {url: $url2}) "
                    "CREATE (n1)-[:CONNECTED]->(n2)",
                    url1=url1,
                    url2=url2,
                )

    # def create_graph(self, set_of_nodes):
    #     with self._driver.session() as session:
    #         session.write_transaction(create_nodes_and_edges, set_of_nodes)

    def get_data_as_json(self):
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (n:URL)-[:CONNECTED]->(m:URL)
                RETURN n.url AS from_node, COLLECT(m.url) AS to_nodes
                """
            )

            data = [
                {
                    "from_node": record["from_node"],
                    "to_nodes": record["to_nodes"],
                }
                for record in result
            ]

        return data

    def clear_graph(self):
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
