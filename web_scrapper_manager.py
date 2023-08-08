import argparse
import json
import os
import re
import time
from urllib.parse import urlparse

from colorama import Fore, Style
from tqdm import tqdm

from custom_errors import *
from royal_road_scraper import RoyalRoadScraper
from utils import timeme
from wattpad_scraper import WattpadScraper


class WebScraperManager:
    """
    A web scraper for novels from supported web fiction sites. It can scrape chapters from sites such as Royal Road
    and ScribbleHub and save them to text files.

    Attributes:
        verbose (bool): Flag to enable or disable verbose mode for more detailed output.
        output_dir (str): Directory to save the scraped fiction (default: current working directory).
        ignore_errors (bool): Flag to ignore errors and continue scraping even if issues are encountered.
        update_mode (bool): Flag to set the mode to update existing scraped fictions.
        rate_limit (float): float deciding the time between scraping of each chapter in seconds
        chapter_limit (int): Integer limiting the number of total scraped chapters per run (across all fictions and sites)

        supported_sites (dict): A dictionary mapping supported web fiction sites (URLs) to their respective scraping
                                functions.
    """
    def __init__(self) -> None:
        """
        Initializes the WebScraper object with default attribute values.
        """

        # Flags and types
        self.flags = {
            "verbose": bool,
            "output_dir": str,
            "ignore_errors": bool,
            "update_mode": bool,
            "rate_limit": float,
            "chapter_limit": int
        }

        # Scraper (class)
        self.scraper = None

        # Total scraped chapters across fictions and scrapers (sites)
        self.total_scraped_chapters = 0

        # Set orange color because not included in colorama
        self.ORANGE = "\033[38;5;202m"

        # Set headers for get requests
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}

        # Supported web fiction sites and their corresponding scraper classes
        # Not supported yet: "https://www.scribblehub.com": ScribbleHubScraper(self)
        self.supported_sites = {
            "https://www.royalroad.com": RoyalRoadScraper(self),
            "https://www.wattpad.com": WattpadScraper(self)
        }

    def run(self) -> None:
        """
        Parses command-line arguments and runs the web scraping process accordingly.

        Returns:
            None
        """
        # Argument Parser
        parser = argparse.ArgumentParser(description=f"Web scraper for online web-novels")

        # Add the arguments for the CLI
        self._add_args(parser)

        # Parse command-line arguments
        args = parser.parse_args()

        # Multiple fictions using JSON configuration
        if args.config:
            with open(args.config, "r") as config_file:
                config = json.load(config_file)

            urls = config["urls"]
            self._set_flags(config)

            # Start the scraping process for the list of URLs from the JSON configuration
            self._config_process(urls_list=urls, verbose=self.verbose)

        # Single fiction case from command-line argument
        elif args.url:
            url = args.url
            self._set_flags(vars(args))

            # Start the scraping process for a single URL from the command-line argument
            self._config_process(urls_list=[url], verbose=self.verbose)

        else:
            # Error message if neither JSON configuration nor URL provided
            parser.error("Please provide either a JSON configuration file using --config or the URL using --url")

        return None

    @staticmethod
    def _add_args(parser: argparse.ArgumentParser) -> None:
        """
        Add command-line arguments to the ArgumentParser object.

        Args:
            parser (argparse.ArgumentParser): The ArgumentParser object to which arguments will be added.

        Returns:
            None
        """
        # String arguments
        parser.add_argument("--url", type=str, nargs='?', help="Full URL of the novel you want to scrape")
        parser.add_argument("--config", type=str,
                            help="Path to the JSON configuration file. If used, overwrites most other command-line arguments")
        parser.add_argument("-o", "--output_dir", type=str, default=None,
                            help="Directory to save the scraped fiction (default: current working directory)")

        # Number arguments
        parser.add_argument("-r", "--rate_limit", type=float, default=.0,
                            help="The rate limit of the scrapper. A float deciding the time between scraping of each chapter in seconds")
        parser.add_argument("-c", "--chapter_limit", type=int,
                            help="Integer limiting the number of total scraped chapters per run (across all fictions and sites)")

        # Action arguments
        parser.add_argument("-u", "--update_mode", action="store_true", help="Set the mode to update")
        parser.add_argument("-v", "--verbose", action="store_true",
                            help="Enable verbose mode for more detailed output")
        parser.add_argument("-i", "--ignore_errors", action="store_true",
                            help="Ignore errors and continue scraping even if issues are encountered")

    def _set_flags(self, config_dict: dict):
        """
        Sets the appropriate flags based on the configuration provided.

        Parameters:
            config_dict (dict): A dictionary containing configuration information.

        Returns:
            None
        """
        for flag_name, flag_type in self.flags.items():
            # Get the value from the configuration dictionary, or set it to None if not provided
            value = config_dict.get(flag_name)

            # Set the corresponding class attribute with the value (cast to the flag type) or None if value is not provided
            setattr(self, flag_name, flag_type(value) if value is not None else None)

        return None

    @timeme
    def _config_process(self, urls_list: list[str], verbose: bool = True) -> None:
        """
        Processes multiple web fictions given a list of URLs.

        Parameters:
            urls_list (list): A list of URLs of the web fictions to process.
            verbose (bool): Flag informing user of execution. Instance variable is passed as an argument to allow decorator access

        Returns:
            None
        """
        # Determine the action based on the update_mode flag
        action = "Updating" if self.update_mode else "Creating"

        # Print the number of novels being processed
        print(f'{action} a total of {len(urls_list)} novel(s).')

        # Loop through the list of URLs and process each web fiction
        for URL in tqdm(urls_list, desc="Scraping novels", unit="novel", ncols=100, disable=verbose):
            try:
                if verbose:
                    # Print the action being performed and the URL of the web fiction
                    print(f"{Fore.RED}{action}: {self.ORANGE}{URL}{Style.RESET_ALL}")

                # Scrape and save the chapters for the current web fiction
                self._scrape_and_save_fiction(fiction_url=URL, verbose=verbose)

            except UnsupportedSiteError as e:
                # Handle the UnsupportedSiteError exception
                # This exception is raised from the internal method if a URL from an unsupported site has been used
                print(e)

                # Check if the ignore_errors flag is set to continue processing other URLs even on error
                if self.ignore_errors:
                    continue

        if verbose:
            print(f"{Fore.LIGHTMAGENTA_EX}Scraped a total of {self.total_scraped_chapters} chapter(s) across {len(urls_list)} fiction(s){Style.RESET_ALL}")

        return None

    @staticmethod
    def _get_order(order_file_path: str) -> str:
        """
        Retrieves the order of chapters from the given order file path.

        Parameters:
            order_file_path (str): The path of the order file containing the scraped chapters.

        Returns:
            str: The order of chapters as a string of URL's. chapters seperated by a linebreak
        """
        # Check if the order file exists
        if os.path.exists(order_file_path):
            # Read the contents of the order file
            with open(order_file_path, "r") as order_file:
                order = order_file.read()
        else:
            # If the order file does not exist, return an empty string
            order = ""

        # Return the order of chapters as a string
        return order

    # TODO.txt: The current fix for deleted fictions is just a print and does not correlate with the exception handling in the specific scrap method
    @timeme
    def _scrape_and_save_fiction(self, fiction_url: str, verbose: bool = True) -> None:
        """
        Scrapes a web fiction given its URL and saves the chapter content to text files.

        Parameters:
            fiction_url (str): The URL of the web fiction to scrape.
            verbose (bool): Flag informing user of execution. Instance variable is passed as an argument to allow decorator access

        Returns:
            None
        """
        master, title, folder_path, chapter_paths = self._scrap_basic(fiction_url)

        # Load the existing order of chapters, if available
        order_file_path = os.path.join(folder_path, "-order.txt")
        order = self._get_order(order_file_path) if self.update_mode else ""

        # Empty string for saving the order of the chapters
        new_order = ""

        # Get the number of chapters
        total_num_chapters = len(chapter_paths)

        # Get number of scraped chapters
        num_scraped = len(order.split("\n")) - 1

        chapters_left = total_num_chapters - num_scraped

        # Disable the progress bar for individual chapters
        disable_prog_bar = False

        # Check if there are any chapters available
        if total_num_chapters == 0:
            if verbose:
                print(f"The fiction at {title} at URL {fiction_url} does not exist or is no longer available.")
            return

        # TODO: Tweak disabling the individual progressbar. When done set instantiation to False
        elif verbose or chapters_left <= 25:
            # Turn off individual progressbars if;
            # verbose, update_mode and the number of chapters yet to be scraped is less than or equal to 50
            disable_prog_bar = True

        # Set total:
        prog_bar_total = self.chapter_limit if self.chapter_limit else chapters_left

        # Loop over each chapter
        for path in tqdm(chapter_paths, desc=f"Scraping chapters of {title}", unit="chapter", ncols=150, disable=disable_prog_bar, total=prog_bar_total, colour="Red"):

            # Check if the chapter has already been scraped in update_mode
            if self.update_mode and (master + path + '\n') in order:
                # if verbose:
                #     print(f"Skipping already scraped chapter: {title}")
                continue

            # Scrape the chapter content and save it to a text file within the subdirectory
            self.scraper.chapter_to_txt(master + path, folder_path)
            if verbose: print(f"{Fore.GREEN}Currently scraping: {self.ORANGE}{master + path}{Style.RESET_ALL}")
            new_order += (master + path) + '\n'

            # Increment the counter after successfully scraping a chapter
            self.total_scraped_chapters += 1

            # Check if the desired limit for chapters scraped per run has been reached
            if self.chapter_limit and self.total_scraped_chapters == self.chapter_limit:
                break

            if self.rate_limit:
                time.sleep(self.rate_limit)

        # Save the updated chapter order to a text file
        with open(order_file_path, "a" if self.update_mode else "w") as order_file:
            order_file.write(new_order)

        return None

    # TODO: maybe assign chapters list as instance-variable (in individual scrappers through master) instead of passing as args multiple times
    def _scrap_basic(self, fiction_url: str) -> tuple[str, str, str, list[str]]:
        """
        Internal function that performs the initial scraping to retrieve the chapters_paths URLs and title of the web fiction.

        Parameters:
            fiction_url (str): The full URL of the web fiction to scrape.

        Returns:
            tuple: A tuple containing the master URL, title of the fiction, folder path for saving the chapters_path, and a list of chapters_path.
        """
        # Create the "Fictions" directory if it doesn't exist
        # fiction_dir = os.path.join(self.output_dir, "Fictions") if self.output_dir else os.path.join(os.getcwd(), "Fictions")
        fiction_dir = os.path.join(self.output_dir if self.output_dir else os.getcwd(), "Fictions")
        os.makedirs(fiction_dir, exist_ok=True)

        # Split the provided URL into master and sub parts
        parsed_url = urlparse(fiction_url)
        master = parsed_url.scheme + "://" + parsed_url.netloc

        # Check for supported sites
        if master not in self.supported_sites:
            raise UnsupportedSiteError(f"Unsupported site: {master}")

        # Get scrapping function for specific site
        self.scraper = self.supported_sites[master]
        chapter_paths, title = self.scraper.scrape_chapters(fiction_url)  # Do stuff

        # Create a folder to store the chapter text files
        folder_name = title.replace(" ", "_")
        folder_name = re.sub(r'[<>:"/\\|?*]', '', folder_name)
        folder_path = os.path.join(fiction_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        return master, title, folder_path, chapter_paths


if __name__ == '__main__':
    print("Please don't run the modules. Only use main.py through commandline args")
