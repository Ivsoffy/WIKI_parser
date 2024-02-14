import argparse
from urllib.parse import quote, unquote
import requests
from bs4 import BeautifulSoup
import logging
import os
from dotenv import load_dotenv
from neo4j_class import Neo4jDriver
from neo4j.exceptions import ConfigurationError
import json
from concurrent.futures import ThreadPoolExecutor


DEFAULT_PAGE = "Erdős number"
DEFAULT_DEPTH = 3
PREFIX_LINK = "https://en.wikipedia.org"
MAX_NUM_NODES = 1000
EXCLUDED_PAGES = [
    "/Portal:",
    "/Wikipedia:",
    "/File:",
    "/Special:",
    "/Template_talk:",
    "/Template:",
    "/Help:",
    "/Category:",
]

visited_pages = set()
set_of_nodes = set()
json_data = []


logging.basicConfig(level=logging.INFO)


def get_args_from_command_line():
    parser = argparse.ArgumentParser(description="Read command line")
    parser.add_argument(
        "-p",
        "--page",
        default=DEFAULT_PAGE,
        type=str,
        help=f"Start wiki page, default={DEFAULT_PAGE}",
        dest="page",
    )
    parser.add_argument(
        "-d",
        "--depth",
        default=DEFAULT_DEPTH,
        type=int,
        help=f"Search depth, default={DEFAULT_DEPTH}",
        dest="depth",
    )
    return parser.parse_args()


def get_auth_info_for_neo4j():
    uri = os.getenv("URI")
    username = os.getenv("USER_NAME")
    password = os.getenv("PASSWORD")
    return uri, username, password


def is_correct_link(link):
    return link.startswith("/wiki/") and not any(
        prefix in link for prefix in EXCLUDED_PAGES
    )


def get_links_from_body(url):
    response = requests.get(url)

    links = []

    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        body = soup.find("div", class_="mw-content-ltr mw-parser-output")
        if body:
            preferences = body.find("ol", class_="references")
            if preferences:
                preferences.decompose()
            navigation = body.find("div", role="navigation")
            if navigation:
                navigation.decompose()
            links = body.find_all("a", href=True)

    return set(
        PREFIX_LINK + quote(link["href"], safe="/:%")
        for link in links
        if is_correct_link(link["href"])
    )


def parse_html(url, depth, driver):
    if (
        depth == 0
        or url in visited_pages
        or len(visited_pages) >= MAX_NUM_NODES
    ):
        return

    # url = f"{PREFIX_LINK}{quote(url, safe='/:%')}"
    logging.info(f"{url} depth={depth}")
    visited_pages.add(url)
    # driver.add_node(unquote(url).replace(" ", "_"))
    # driver.add_node(url)

    links = get_links_from_body(url)
    if links:
        json_data.append(
            {
                "from_node": {
                    "title": unquote(
                        url.replace(f"{PREFIX_LINK}/wiki/", "")
                    ).replace("_", " "),
                    "link": url,
                },
                "to_nodes": [
                    {
                        "title": unquote(
                            link.replace(f"{PREFIX_LINK}/wiki/", "").replace(
                                "_", " "
                            )
                        ),
                        "link": link,
                    }
                    for link in links
                ],
            }
        )

    for link in links:
        set_of_nodes.add(
            (
                url,
                link,
            )
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(parse_html, link, depth - 1, driver)
            for link in links
            if len(visited_pages) < MAX_NUM_NODES
            and f"{PREFIX_LINK}{link}" not in visited_pages
            and depth - 1 != 0
        ]
        for future in futures:
            future.result()


def main():
    args = get_args_from_command_line()

    load_dotenv()
    try:
        uri, username, password = get_auth_info_for_neo4j()
        driver = Neo4jDriver(uri, username, password)
        driver.clear_graph()

        start_page, depth = (
            PREFIX_LINK + "/wiki/" + quote(args.page, safe="/:%"),
            args.depth if args.depth > 0 else DEFAULT_DEPTH,
        )
        parse_html(start_page, depth, driver)
        # for node in set_of_nodes:
        #     print(node)
        # print(f"edges = {len(set_of_nodes)}")
        # driver.create_graph(set_of_nodes)

        # json_data = driver.get_data_as_json()

        with open("graph.json", "w") as file:
            json.dump(json_data, file, indent=2)

        os.environ["WIKI_FILE"] = "graph.json"

        driver.close()
        # print(f"nodes = {len(set_of_nodes)}")

    except ConfigurationError:
        logging.error("Incorrect auth for neo4j")


if __name__ == "__main__":
    main()
