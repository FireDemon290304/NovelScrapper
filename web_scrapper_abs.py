from abc import ABC, abstractmethod


class WebScrapper(ABC):
    @abstractmethod
    def scrape_chapters(self, fiction_url: str) -> tuple[list, str]:
        """
        Scrapes the general information of a fiction from the given URL

        Args:
            fiction_url (str): url for the main page of the fiction

        Returns:
            A tuple containing a list of urls of the chapters in the fiction, followed by the fiction title
        """
        pass

    @abstractmethod
    def chapter_to_txt(self, url: str = None, folder_name: str = None) -> None:
        """
        Scrapes the content of a chapter from the given URL and saves it to a text file within the provided subdirectory.

        Args:
            url (str): The URL of the chapter.
            folder_name (str): The name of the subdirectory to save the text file.

        Returns:
            None
        """
        pass
