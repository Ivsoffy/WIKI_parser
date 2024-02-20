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
MAX_NUM_VISITED_PAGES = 1000
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

num_visited_pages = 0
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
    parser.add_argument(
        "-n",
        "--num",
        default=MAX_NUM_VISITED_PAGES,
        type=int,
        help=f"Maximum number of pages visited, default={MAX_NUM_VISITED_PAGES}",
        dest="num",
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
    links = []

    response = requests.get(f"{PREFIX_LINK}{url}")
    if response.ok:
        soup = BeautifulSoup(response.text, "lxml")
        body = soup.find("div", class_="mw-content-ltr mw-parser-output")
        if body:
            remove_contents_from_body(body)
            links = body.find_all("a", href=True)

    return set(link for link in links if is_correct_link(link["href"]))


def parse_html(url, depth, driver):
    global visited_pages, json_data, num_visited_pages

    if (
        depth == 0
        or url in visited_pages
        or len(visited_pages) >= num_visited_pages
    ):
        return

    visited_pages.add(url)
    logging.info(f"PAGE:{PREFIX_LINK}{url}")

    links = get_links_from_body(url)
    if links:
        node = {
            "from_node": {
                "title": unquote(url.replace(f"/wiki/", "")).replace("_", " "),
                "link": f"{PREFIX_LINK}{url}",
            },
            "to_nodes": [
                {
                    "title": link.get("title"),
                    "link": quote(f"{PREFIX_LINK}{link['href']}", safe="/:%"),
                }
                for link in links
            ],
        }

        json_data.append(node)
        driver.create_graph(node)

        with ThreadPoolExecutor(max_workers=min(4, os.cpu_count())) as executor:
            futures = [
                executor.submit(
                    parse_html,
                    quote(link["href"], safe="/:%"),
                    depth - 1,
                    driver,
                )
                for link in links
                if len(visited_pages) < num_visited_pages
                and link not in visited_pages
                and depth - 1 != 0
            ]

            for future in futures:
                future.result()


def get_start_page_and_depth(args):
    return (
        quote("/wiki/" + args.page.replace(" ", "_"), safe="/:%"),
        args.depth if args.depth > 0 else DEFAULT_DEPTH,
    )


def save_json(json_data):
    with open("./graph.json", "w") as file:
        json.dump(json_data, file, indent=2)


def add_wiki_file_in_env():
    if os.getenv("WIKI_FILE") is None:
        os.environ["WIKI_FILE"] = "graph.json"
        with open("./.env", "a") as env_file:
            env_file.write("WIKI_FILE=graph.json\n")


def main():
    global json_data, num_visited_pages

    args = get_args_from_command_line()
    num_visited_pages = args.num

    load_dotenv()
    try:
        uri, username, password = get_auth_info_for_neo4j()
        driver = Neo4jDriver(uri, username, password)
        driver.clear_graph()

        start_page, depth = get_start_page_and_depth(args)
        parse_html(start_page, depth, driver)
        save_json(json_data)
        add_wiki_file_in_env()

        driver.close()

    except ConfigurationError:
        logging.error("Incorrect auth for neo4j")


if __name__ == "__main__":
    main()
