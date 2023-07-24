from web_scrapper_abs import WebScrapper


class ScribbleHubScrapper(WebScrapper):
    def __init__(self, manager):
        self.manager = manager

    def scrape_chapters(self, fiction_url: str) -> tuple[list, str]:
        pass

    def chapter_to_txt(self, url: str = None, folder_name: str = None) -> None:
        pass
