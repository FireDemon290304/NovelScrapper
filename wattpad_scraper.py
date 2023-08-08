import re

import requests
from bs4 import BeautifulSoup

from web_scraper_abstract import WebScraper


class WattpadScraper(WebScraper):
    # API_GETCATEGORIES = 'https://www.wattpad.com/apiv2/getcategories'
    # API_CHAPTERINFO = 'https://www.wattpad.com/v4/parts/%s?fields=group(id)&_=%s'
    API_STORYINFO = 'https://www.wattpad.com/api/v3/stories/%s'  # stories?id=X is NOT the same
    API_STORYTEXT = 'https://www.wattpad.com/apiv2/storytext?id=%s'

    fiction_info_json = None

    def scrape_chapters(self, fiction_url: str) -> tuple[list[str], str]:
        # Send a GET request to the webpage
        story_id = re.search(r".com/story/(\d+)", fiction_url).group(1)

        response = requests.get(self.API_STORYINFO % story_id, headers=self.manager.headers)
        response.raise_for_status()

        chapter_paths = []
        title = ""

        try:
            self.fiction_info_json = response.json()
            title = self.fiction_info_json["title"]
            parts = self.fiction_info_json["parts"]

            # common_prefix = 'https://www.wattpad.com'
            # common_prefix (protocol + domain) is always 23 characters
            chapter_paths = [part["url"][23:] for part in parts]

        except AttributeError as e:
            print(e)
            if not self.manager.ignore_errors:
                raise

        return chapter_paths, title

    def chapter_to_txt(self, url: str = None, folder_path: str = None) -> None:
        # Send a GET request to the webpage
        story_id = re.search(r".com/(\d+)", url).group(1)
        response = requests.get(self.API_STORYTEXT % story_id, headers=self.manager.headers)
        response.raise_for_status()

        # Create a BeautifulSoup object from the response text
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all paragraph elements
        paragraphs = soup.find_all("p")

        # Get the name of the chapter through the fiction info json
        chap_name = ""
        for part in self.fiction_info_json["parts"]:
            if part["url"] == url:
                chap_name = part["title"]

        # Alternative
        # found_part = next((part for part in self.fiction_info_json["parts"] if part["url"] == url))
        # filename = found_part["title"]

        # Generate the filepath for the text file
        file_path, chapter_name = self.gen_filepath(folder_path, chap_name)

        # Writing the chapter content to the text file within the subdirectory
        # Can be found in super, as both currently are the same
        self.try_write(file_path, paragraphs, chapter_name)

        return None
