from web_scrapper_manager import WebScrapper


class RoyalRoadScrapper(WebScrapper):
    def scrape_chapters(self, fiction_url: str) -> tuple[list, str]:
        pass

    def chapter_to_txt(self, url: str = None, folder_name: str = None) -> None:
        pass
