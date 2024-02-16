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
import time


DEFAULT_PAGE = "Erdős number"
DEFAULT_DEPTH = 3
PREFIX_LINK = "https://en.wikipedia.org"
MAX_NUM_NODES = 1000
EXCLUDED_PAGES = [
    "/Portal:",
    "/Wikipedia:",
    "/Special:",
    "/File:",
    "/Help:",
]
TAGS_TO_REMOVE = [
    {"name": "ol", "class": "references"},
    {"name": "div", "role": "navigation"},
    {"name": "sup", "class": "reference"},
    {"name": "div", "role": "note"},
    {"name": "figure"},
    {"name": "table"},
    {"name": "div", "class": "catlinks"},
    {"name": "span", "class": "rt-commentedText nowrap"},
    {"name": "span", "class": "mw-editsection"},
    {"name": "style"},
]

visited_pages = set()
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


def remove_contents_from_body(body):
    for tag_info in TAGS_TO_REMOVE:
        tag = tag_info["name"]
        attrs = {key: value for key, value in tag_info.items() if key != "name"}
        element = body.find(tag, attrs)
        while element:
            element.decompose()
            element = body.find(tag, attrs)

    reflist = body.find(
        "div", class_=lambda value: value and "reflist" in value
    )
    if reflist:
        for sibling in reflist.find_next_siblings():
            sibling.extract()
        reflist.decompose()
    return body


def get_links_from_body(url):
    response = requests.get(url)

    links = []

    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        body = soup.find("div", class_="mw-content-ltr mw-parser-output")
        if body:
            remove_contents_from_body(body)
            links = body.find_all("a", href=True)

    return set(
        PREFIX_LINK + quote(link["href"], safe="/:%")
        for link in links
        if is_correct_link(link["href"])
    )


def parse_html(url, depth, driver):
    global visited_pages, json_data

    if (
        depth == 0
        or url in visited_pages
        or len(visited_pages) >= MAX_NUM_NODES
    ):
        return

    visited_pages.add(url)

    links = get_links_from_body(url)
    logging.info(f"PAGE:{url}")

    if links:
        node = {
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

        json_data.append(node)
        driver.create_graph(node)

        with ThreadPoolExecutor(max_workers=min(4, os.cpu_count())) as executor:
            futures = [
                executor.submit(parse_html, link, depth - 1, driver)
                for link in links
                if len(visited_pages) < MAX_NUM_NODES
                and link not in visited_pages
                and depth - 1 != 0
            ]

            for future in futures:
                future.result()
        # for link in links:
        #     parse_html(link, depth - 1, driver)


def main():
    global json_data

    start_time = time.time()

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

        with open("graph.json", "w") as file:
            json.dump(json_data, file, indent=2)

        os.environ["WIKI_FILE"] = "graph.json"

        driver.close()

    except ConfigurationError:
        logging.error("Incorrect auth for neo4j")

    end_time = time.time()

    print(f"time = {end_time - start_time}")


if __name__ == "__main__":
    main()
