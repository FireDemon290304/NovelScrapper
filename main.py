from single_chapter import *
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import timeme
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import argparse
import json
import requests
import re
import os


@timeme
def create_fiction(fiction_url):
    master, folder_path, chapters = _scrap(fiction_url)

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
def update_fiction(fiction_url):
    master, folder_path, chapters = _scrap(fiction_url)

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
    with open(order_file_path, "w") as order_file:
        order_file.write(order)


def _scrap(fiction_url):
    # Create the "Fictions" directory if it doesn't exist
    fiction_dir = os.path.join(os.getcwd(), "Fictions")
    os.makedirs(fiction_dir, exist_ok=True)

    # Split the provided URL into master and sub parts
    parsed_url = urlparse(fiction_url)
    master = parsed_url.scheme + "://" + parsed_url.netloc

    # Check for supported sites
    if master not in supported_sites:
        raise ValueError(f"Unsupported site: {master}")

    # Get scrapping function for specific site
    scraping_function = supported_sites[master]
    chapters, title = scraping_function(fiction_url)  # Do stuff

    # Create a folder to store the chapter text files
    folder_name = title.replace(" ", "_")  # .replace(".", "-").replace(",", "-")
    folder_name = re.sub(r'[<>:"/\\|?*]', '', folder_name)
    folder_path = os.path.join(fiction_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    return master, folder_path, chapters


def _scrap_rr(fiction_url):
    # Send a GET request to the webpage
    response = requests.get(fiction_url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all chapter rows
    chapters = soup.find_all(class_="chapter-row")

    # Get the title of the novel
    title = soup.find("h1").get_text()

    return chapters, title


def _scrap_sh(fiction_url):
    # TODO: use selenium because js sucks -_-
    fiction_url += ""
    # webdriver_path = r""
    # opera_binary_path = r""

    # selenium_options = webdriver.ChromeOptions()
    # selenium_options.binary_location = opera_binary_path
    # selenium_options.add_argument('--headless')  # Run Chrome in headless mode (without opening a browser window)
    # service = Service(webdriver_path)
    # driver = webdriver.Chrome(service=service, options=selenium_options)
    #
    # wait = WebDriverWait(driver, 5)  # Wait for a maximum of 5 seconds
    #
    # Find all chapter rows
    # chapters_table = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="review_new_tab"]/div[2]/div/ol')))
    # print(chapters_table)
    # chapters = ""
    #
    # Get the title of the novel
    # title_element = wait.until(EC.visibility_of_element_located((By.XPATH, "//div[@class='fic_title']")))
    # title = title_element.text
    #
    # return chapters, title


@timeme
def config_update(urls_list):
    print(f'Updating a total of {len(urls_list)} novel(s).')
    for URL in urls_list:
        print(f"Updating: {URL}")
        update_fiction(URL)


@timeme
def config_create(urls_list):
    print(f'Creating a total of {len(urls_list)} novel(s).')
    for URL in urls_list:
        try:
            print(f"Creating: {URL}")
            create_fiction(URL)
        except ValueError:
            print("Unsupported site\n"
                  f"URL: {URL}")
            continue


if __name__ == '__main__':
    supported_sites = {"https://www.royalroad.com": _scrap_rr,
                       "https://www.scribblehub.com": _scrap_sh}
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
        parser.error(
            "Please provide either a JSON configuration file using --config or the URL using --create or --update")
