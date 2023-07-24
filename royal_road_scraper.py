from web_scrapper_abs import WebScrapper
from bs4 import BeautifulSoup
import requests
import re
import os


class RoyalRoadScrapper(WebScrapper):
    def __init__(self, manager):
        self.manager = manager

    def scrape_chapters(self, fiction_url: str) -> tuple[list, str]:
        # Send a GET request to the webpage
        response = requests.get(fiction_url)
        soup = BeautifulSoup(response.text, "html.parser")

        chapters = []
        title = ""

        try:
            # Find all chapter rows
            chapters = soup.find_all(class_="chapter-row")

            # Get the title of the novel
            title = soup.find("h1").get_text()

        except AttributeError as e:
            if not self.manager.ignore_errors:
                print("Unable to retrieve fiction title: ", e)
                site_error_msg = soup.find(class_="col-md-12 page-404")
                msg = site_error_msg.find("p")
                print(msg.get_text())
                raise

        return chapters, title

    def chapter_to_txt(self, url: str = None, folder_name: str = None) -> None:
        # Send a GET request to the webpage
        response = requests.get(url)

        # Create a BeautifulSoup object from the response text
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the div element with the class "chapter-inner chapter-content"
        div_element = soup.find("div", class_="chapter-inner chapter-content")

        # Find all paragraph elements within the div
        paragraphs = div_element.find_all("p")

        # Generate the filepath for the text file
        file_path, filename = self._gen_filepath(folder_name, soup)

        # Writing the chapter content to the text file within the subdirectory
        try:
            with open(file_path + ".txt", 'w', encoding='utf-8') as file:
                for paragraph in paragraphs:
                    file.write(f'{paragraph.get_text()}\n')
        except OSError:
            print(f"Failed to convert {filename} to txt.")

        return None

    @staticmethod
    def _gen_filepath(folder_name: str, soup=None) -> tuple[str, str]:
        """
        Generates the file path for the text file based on the subdirectory and chapter title.

        Args:
            folder_name (str): The name of the subdirectory.
            soup (BeautifulSoup): The BeautifulSoup object representing the HTML content.

        Returns:
            str: The full file path for the text file.
        """
        filename = soup.find("h1").get_text()

        # Remove disallowed characters from the filename
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Limit the filename length to 255 characters
        filename = filename[:255]

        # Creating the full path for the text file
        return os.path.join(folder_name, filename), filename
