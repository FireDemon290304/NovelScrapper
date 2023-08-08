import os
import re
from abc import ABC, abstractmethod
from typing import final

import bs4


class WebScraper(ABC):
    @final
    def __init__(self, manager):
        """
        Defines the manager/owner of the scrapper
        Args:
            manager (WebScrapperManager): An instance of the WebScrapperManager class that manages the overall web scraping process.
        """
        self.manager = manager

    @final
    def try_write(self, file_path: str, paragraphs: bs4.element.ResultSet, chapter_name: str) -> None:
        """
        Attempt to write paragraphs to a text file.

        This method attempts to write the contents of the provided paragraphs to a text
        file specified by the given file path. Each paragraph is written on a new line.

        Args:
            file_path (str): The path to the file where paragraphs will be written.
            paragraphs (list): A list of paragraph objects or strings to be written.
            chapter_name (str): The name of the chapter being processed.

        Raises:
            OSError: If there is an issue with writing to the file.

        Note:
            If the writing operation fails, the behavior depends on the `verbose` and
            `ignore_errors` settings of the manager associated with this instance. If
            `verbose` is True, a message about the failure will be printed. If
            `ignore_errors` is False, the exception will be re-raised.

        """
        try:
            with open(file_path + ".txt", 'w', encoding='utf-8') as file:
                for paragraph in paragraphs:
                    file.write(f'{paragraph.get_text()}\n')
        except OSError:
            if self.manager.verbose:
                print(f"Failed to convert {chapter_name} to txt.")
            if not self.manager.ignore_errors:
                raise

        return None

    @final
    def gen_filepath(self, folder_name: str, chapter_name: str) -> tuple[str, str]:
        """
        Generates the file path for the text file based on the subdirectory and chapter URL.

        Args:
            folder_name (str): Name of the subdirectory.
            chapter_name (str): Name of the chapter.

        Returns:
            tuple: A tuple containing the full file path and the filename.
        """
        # Remove disallowed characters from the filename
        chapter_name = re.sub(r'[<>:"/\\|?*]', '', chapter_name)

        # Limit the filename length to 255 characters
        chapter_name = chapter_name[:255]

        # Creating the full path for the text file
        return os.path.join(folder_name, chapter_name), chapter_name

    @abstractmethod
    def scrape_chapters(self, fiction_url: str) -> tuple[list[str], str]:
        """
        Scrapes the general information of a fiction from the given URL

        Args:
            fiction_url (str): url for the main page of the fiction (not individual chapters)

        Returns:
            A tuple containing a list of paths to the chapters in the fiction, followed by the fiction title.
            The paths should exclude the "master" (http(s)://site.something) and only include "/path_to_fiction
            Example: /834112711-fiction_title-chapter-1
        """
        pass

    @abstractmethod
    def chapter_to_txt(self, url: str = None, folder_path: str = None) -> None:
        """
        Scrapes the content of a chapter from the given URL and saves it to a text file within the provided subdirectory.

        Args:
            url (str): The URL of the chapter.
            folder_path (str): The full path of the subdirectory in which to save the text file.

        Returns:
            None
        """
        pass
