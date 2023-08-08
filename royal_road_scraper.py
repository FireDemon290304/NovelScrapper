from bs4 import BeautifulSoup
import requests

from web_scraper_abstract import WebScraper


class RoyalRoadScraper(WebScraper):
    """
    A web scraper for novels from Royal Road, a web fiction site. It inherits from the WebScraper class, which is an
    abstract base class providing a common interface for web scraping.

    Attributes:
        manager (WebScrapperManager): An instance of the WebScrapperManager class that manages the overall web scraping process.

    Methods:
        __init__(self, manager: WebScrapperManager) -> None: Initializes the RoyalRoadScraper object with the manager instance.
        scrape_chapters(self, fiction_url: str) -> tuple[list, str]: Scrapes the chapters and title of a web fiction from Royal Road.
        chapter_to_txt(self, url: str = None, folder_name: str = None) -> None: Scrapes a chapter content from the provided URL
                                                                                 and saves it to a text file within the subdirectory.
        _gen_filepath(folder_name: str, soup=None) -> tuple[str, str]: Generates the file path for the text file based on the
                                                                      subdirectory and chapter title.
    """
    def scrape_chapters(self, fiction_url: str) -> tuple[list[str], str]:
        # Send a GET request to the webpage
        response = requests.get(fiction_url, headers=self.manager.headers)
        response.raise_for_status()

        # Create soup object
        soup = BeautifulSoup(response.text, "html.parser")

        chapter_paths = []
        title = ""

        try:
            # Find all chapter rows
            chapter_paths = soup.find_all(class_="chapter-row")

            # Convert ResultSet to list of strings
            chapter_paths = [i.find("a")["href"] for i in chapter_paths]

            # Get the title of the novel
            title = soup.find("h1").get_text()

        except AttributeError as e:
            if not self.manager.ignore_errors:
                print("Unable to retrieve fiction info: ", e)
                site_error_msg = soup.find(class_="col-md-12 page-404")
                msg = site_error_msg.find("p")
                print(msg.get_text())
                raise

        return chapter_paths, title

    def chapter_to_txt(self, url: str = None, folder_path: str = None) -> None:
        # Send a GET request to the webpage
        response = requests.get(url)

        # Create a BeautifulSoup object from the response text
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the div element with the class "chapter-inner chapter-content"
        div_element = soup.find("div", class_="chapter-inner chapter-content")

        # Find all paragraph elements within the div
        paragraphs = div_element.find_all("p")

        chapter_name = soup.find("h1").get_text()

        # Generate the filepath for the text file
        file_path, chapter_name = self.gen_filepath(folder_path, chapter_name)

        # Writing the chapter content to the text file within the subdirectory
        self.try_write(file_path, paragraphs, chapter_name)

        return None
