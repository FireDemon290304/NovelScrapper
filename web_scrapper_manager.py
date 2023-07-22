from abc import ABC, abstractmethod
from single_chapter import chapter_to_txt
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from utils import timeme
from tqdm import tqdm
import argparse
import json
import requests
import re
import os


class WebScrapper(ABC):
    @abstractmethod
    def scrape_chapters(self, fiction_url: str) -> tuple[list, str]:
        pass

    @abstractmethod
    def chapter_to_txt(self, url: str = None, folder_name: str = None) -> None:
        pass


class WebScrapperManager:
    """
    A web scraper for novels from supported web fiction sites. It can scrape chapters from sites such as Royal Road
    and ScribbleHub and save them to text files.

    Attributes:
        verbose (bool): Flag to enable or disable verbose mode for more detailed output.
        output_dir (str): Directory to save the scraped fiction (default: current working directory).
        ignore_errors (bool): Flag to ignore errors and continue scraping even if issues are encountered.
        update_mode (bool): Flag to set the mode to update existing scraped fictions.

        supported_sites (dict): A dictionary mapping supported web fiction sites (URLs) to their respective scraping
                                functions.

    Methods:
        __init__(): Initializes the WebScrapper object with default attribute values.
        run(): Parses command-line arguments and runs the web scraping process accordingly.
        _get_order(order_file_path: str) -> str: Retrieves the order of chapters from the given order file path.
        _scrape_and_save_fiction(fiction_url: str, verbose: bool = True) -> None: Scrapes a web fiction given its URL
                                                                                  and saves the chapter content to text
                                                                                  files.
        config_process(urls_list: list, verbose: bool = True) -> None: Processes multiple web fictions given a list
                                                                       of URLs.
        _scrap_basic(fiction_url: str) -> tuple[str, str, list]: Performs the initial scraping to retrieve the
                                                                chapters' URLs and title of the web fiction.
        _scrap_rr(fiction_url: str) -> tuple[list, str]: Scrapes chapters and the title of a web fiction from Royal Road.
        _scrap_sh(fiction_url: str) -> None: Scrapes chapters and the title of a web fiction from ScribbleHub.
    """
    def __init__(self) -> None:
        """
        Initializes the WebScrapper object with default attribute values.

        Attributes:
            self.verbose (bool): Flag to enable or disable verbose mode for more detailed output.
            self.output_dir (str): Directory to save the scraped fiction (default: current working directory).
            self.ignore_errors (bool): Flag to ignore errors and continue scraping even if issues are encountered.
            self.update_mode (bool): Flag to set the mode to update existing scraped fictions.

            self.supported_sites (dict): A dictionary mapping supported web fiction sites (URLs) to their respective scraping
                                         functions.
        """
        self.verbose = bool
        self.output_dir = str
        self.ignore_errors = bool
        self.update_mode = bool

        self.supported_sites = {"https://www.royalroad.com": self._scrap_rr,
                                "https://www.scribblehub.com": self._scrap_sh}

    def run(self) -> None:
        """
        Parses command-line arguments and runs the web scraping process accordingly.

        Returns:
            None
        """
        # Parser
        parser = argparse.ArgumentParser(description="Web scraper for novels\nSupports Royal Road &")

        # String args
        parser.add_argument("--url", type=str, nargs='?', help="Full URL of the novel you want to scrap")
        parser.add_argument("--config", type=str,
                            help="Path to the JSON configuration file. If used, overwrites most other commandline arguments")
        parser.add_argument("-o", "--output_dir", type=str, default=None,
                            help="Directory to save the scraped fiction (default: current working directory)")

        # Action args
        parser.add_argument("-u", "--update", action="store_true", help="set the mode to update")
        parser.add_argument("-v", "--verbose", action="store_true",
                            help="Enable verbose mode for more detailed output")
        parser.add_argument("-i", "--ignore_errors", action="store_true",
                            help="Ignore errors and continue scraping even if issues are encountered")

        # Args
        args = parser.parse_args()

        # Multiple fictions using json
        if args.config:
            with open(args.config, "r") as config_file:
                config = json.load(config_file)

            # Check if 'urls' and 'mode' keys exist in the config
            urls = config["urls"]
            self.verbose = config["verbose"]
            self.ignore_errors = config["ignore_errors"]
            self.output_dir = config["output_dir"]
            self.update_mode = config["update_mode"]

            self._config_process(urls_list=urls, verbose=self.verbose)

        # Single fiction case
        elif args.url:
            url = args.url
            self.verbose = args.verbose
            self.ignore_errors = args.ignore_errors
            self.output_dir = args.output_dir
            self.update_mode = args.update

            self._config_process(urls_list=[url], verbose=self.verbose)

        else:
            parser.error(
                "Please provide either a JSON configuration file using --config or the URL using --url")

    @staticmethod
    def _get_order(order_file_path: str) -> str:
        """
        Retrieves the order of chapters from the given order file path.

        Parameters:
            order_file_path (str): The path of the order file containing the scraped chapters.

        Returns:
            str: The order of chapters as a string.
        """
        if os.path.exists(order_file_path):
            with open(order_file_path, "r") as order_file:
                order = order_file.read()
        else:
            order = ""
        return order

    @timeme
    def _scrape_and_save_fiction(self, fiction_url: str, verbose: bool = True) -> None:
        # TODO.txt: The current fix for deleted fictions is just a print and does not correlate with the exception handling in the specific scrap method
        """
        Scrapes a web fiction given its URL and saves the chapter content to text files.

        Parameters:
            fiction_url (str): The URL of the web fiction to scrape.
            verbose (bool): Flag informing user of execution. Instance variable is passed as an argument to allow decorator access

        Returns:
            None
        """
        master, folder_path, chapters = self._scrap_basic(fiction_url)

        # Load the existing order of chapters, if available
        order_file_path = os.path.join(folder_path, "-order.txt")
        order = self._get_order(order_file_path) if self.update_mode else ""

        # Empty string for saving the order of the chapters
        new_order = ""

        # Check if there are any chapters available
        if len(chapters) == 0:
            print(f"The fiction at {fiction_url} does not exist or is no longer available.")
            return

        # Loop over each chapter
        for chapter in chapters:
            link = chapter.find("a")
            chapter_url = link["href"]

            # Check if the chapter has already been scraped
            if self.update_mode and (master + chapter_url + '\n') in order:
                continue

            # Scrape the chapter content and save it to a text file within the subdirectory
            chapter_to_txt(master + chapter_url, folder_path)
            if verbose:
                print(master + chapter_url)
            new_order += (master + chapter_url) + '\n'

        # Save the updated chapter order to a text file
        with open(order_file_path, "a" if self.update_mode else "w") as order_file:
            order_file.write(new_order)

    @timeme
    def _config_process(self, urls_list: list, verbose: bool = True) -> None:
        """
        Processes multiple web fictions given a list of URLs.

        Parameters:
            urls_list (list): A list of URLs of the web fictions to process.
            verbose (bool): Flag informing user of execution. Instance variable is passed as an argument to allow decorator access

        Returns:
            None
        """
        action = "Updating" if self.update_mode else "Creating"
        print(f'{action} a total of {len(urls_list)} novel(s).')
        for URL in tqdm(urls_list, desc="Scraping novels", unit="novel", ncols=100, disable=verbose):
            try:
                if verbose: print(f"{action}: {URL}")
                self._scrape_and_save_fiction(URL, verbose=verbose)
            except ValueError:
                print("Unsupported site\n"
                      f"URL: {URL}")
                continue

    def _scrap_basic(self, fiction_url: str) -> tuple[str, str, list]:
        """
        Internal function that performs the initial scraping to retrieve the chapters' URLs and title of the web fiction.

        Parameters:
            fiction_url (str): The URL of the web fiction to scrape.

        Returns:
            tuple: A tuple containing the master URL, folder path for saving the chapters, and a list of chapters.
        """
        # Create the "Fictions" directory if it doesn't exist
        fiction_dir = os.path.join(str(self.output_dir), "Fictions") if self.output_dir else os.path.join(os.getcwd(), "Fictions")
        os.makedirs(fiction_dir, exist_ok=True)

        # Split the provided URL into master and sub parts
        parsed_url = urlparse(fiction_url)
        master = parsed_url.scheme + "://" + parsed_url.netloc

        # Check for supported sites
        if master not in self.supported_sites:
            raise ValueError(f"Unsupported site: {master}")

        # Get scrapping function for specific site
        scraping_function = self.supported_sites[master]
        chapters, title = scraping_function(fiction_url)  # Do stuff

        # Create a folder to store the chapter text files
        folder_name = title.replace(" ", "_")
        folder_name = re.sub(r'[<>:"/\\|?*]', '', folder_name)
        folder_path = os.path.join(fiction_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        return master, folder_path, chapters

    def _scrap_rr(self, fiction_url: str) -> tuple[list, str]:
        """
        Internal function that scrapes chapters and the title of a web fiction from Royal Road.

        Parameters:
            fiction_url (str): The URL of the web fiction to scrape.

        Returns:
            tuple: A tuple containing a list of chapters and the title of the web fiction.
        """
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
            if not self.ignore_errors:
                print("Unable to retrieve fiction title: ", e)
                site_error_msg = soup.find(class_="col-md-12 page-404")
                msg = site_error_msg.find("p")
                print(msg.get_text())
                raise

        return chapters, title

    def _scrap_sh(self, fiction_url: str) -> tuple[list, str]:
        """
        Internal function that scrapes chapters and the title of a web fiction from ScribbleHub.

        Parameters:
            fiction_url (str): The URL of the web fiction to scrape.

        Returns:
            None
        """

        # TODO.txt: use selenium because js sucks -_-
        self.verbose = True
        fiction_url += ""

        return [], ""


if __name__ == '__main__':
    print("Please don't run the modules, only main.py takes commandline args")