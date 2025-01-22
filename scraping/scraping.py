"""
This file contains the class responsible for scraping football match data.
"""
import requests


class Scraper:
    """
    This is the parent Scraper class
    """
    main_url: str
    
    def __init__(self) -> None:
        """Initializer for Scraper"""
        self.main_url = "https://fbref.com/en/"


class MatchScraper(Scraper):
    """
    This is the child class of the Scraper class responsible for scrapping match data.
    """
    match_url: str

    def __init__(self) -> None:
        """Initializer for MatchScrapper"""
        # This is necessary to call the parent function's init method
        super().__init__()
        self.match_url = self.main_url + "comps/9/Premier-League-Stats"



class PlayerScraper(Scraper):
    """
    This is the child class of the Scraper class responsible for scrapping player data.
    """

    pass


if __name__ == "__main__":
    scraper = Scraper()
    match_scraper = MatchScraper()
    print(match_scraper.main_url)