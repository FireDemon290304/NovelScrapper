from single_chapter import *
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import timeme
import argparse
import json
import requests
import re
import os


@timeme
def create_fiction(do_url):
    master, folder_path, chapters = _scrap(do_url)

    # Empty string for saving the order of the chapters
    order = ""

    # Loop over each chapter
    for chapter in chapters:
        link = chapter.find("a")
        chapter_url = link["href"]

        # Scrape the chapter content and save it to a text file within the subdirectory
        chapter_to_txt(master + chapter_url, folder_path)
        print(master + chapter_url)
        order += (master + chapter_url) + '\n'

    order_file_path = os.path.join(folder_path, "-order.txt")

    # Save the chapter order to a text file
    with open(order_file_path, "w") as temp:
        temp.write(order)


@timeme
def update_fiction(do_url):
    master, folder_path, chapters = _scrap(do_url)

    # Load the existing order of chapters, if available
    order_file_path = os.path.join(folder_path, "-order.txt")
    if os.path.exists(order_file_path):
        with open(order_file_path, "r") as order_file:
            order = order_file.read()
    else:
        order = ""

    # Loop over each chapter
    for chapter in chapters:
        link = chapter.find("a")
        chapter_url = link["href"]

        # Check if the chapter has already been scraped
        if (master + chapter_url + '\n') in order:
            continue

        # Scrape the chapter content and save it to a text file within the subdirectory
        chapter_to_txt(master + chapter_url, folder_path)
        print(master + chapter_url)
        order += (master + chapter_url) + '\n'

    # Save the updated chapter order to a text file
    with open(order_file_path, "w") as temp:
        temp.write(order)


def _scrap(do_url):
    # Split the provided URL into master and sub parts
    parsed_url = urlparse(do_url)
    master = parsed_url.scheme + "://" + parsed_url.netloc
    sub = parsed_url.path

    # Send a GET request to the webpage
    response = requests.get(url=master + sub)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all chapter rows
    chapters = soup.find_all(class_="chapter-row")

    # Get the title of the novel
    title = soup.find("h1").get_text()

    # Create the "Fictions" directory if it doesn't exist
    fiction_dir = os.path.join(os.getcwd(), "Fictions")
    os.makedirs(fiction_dir, exist_ok=True)

    # Create a folder to store the chapter text files
    folder_name = title.replace(" ", "_")
    folder_name = re.sub(r'[<>:"/\\|?*]', '', folder_name)
    folder_path = os.path.join(fiction_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    return master, folder_path, chapters


@timeme
def config_update(urls_list):
    for URL in urls_list:
        print(f"Updating: {URL}")
        update_fiction(URL)


@timeme
def config_create(urls_list):
    for URL in urls_list:
        print(f"Creating: {URL}")
        create_fiction(URL)


if __name__ == '__main__':
    supported_sites = {"https://www.royalroad.com", "https://www.scribblehub.com"}
    parser = argparse.ArgumentParser(description="Web scraper for novels\nSupports Royal Road &")
    parser.add_argument("--config", type=str, help="Path to the JSON configuration file")
    parser.add_argument("--create", type=str, help="Full URL of the novel you want to scrap")
    parser.add_argument("--update", type=str, help="Full URL of the novel you want to update")

    args = parser.parse_args()

    if args.config:
        with open(args.config, "r") as config_file:
            config = json.load(config_file)

        # Check if 'urls' and 'mode' keys exist in the config
        if "urls" in config and isinstance(config["urls"], list) and "mode" in config:
            urls = config["urls"]
            mode = config["mode"]

            if mode == "create":
                config_create(urls)
            elif mode == "update":
                config_update(urls)
            else:
                parser.error("Invalid mode specified in the config. Please use 'create' or 'update'.")
        else:
            parser.error("Error: 'urls' or 'mode' do not exist in the config, or have been incorrectly modified")

    elif args.create:
        create_fiction(args.create)

    elif args.update:
        update_fiction(args.update)

    else:
        parser.error("Please provide either a JSON configuration file using --config or the URL using --create or --update")
