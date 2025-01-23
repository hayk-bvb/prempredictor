"""
This file contains the class responsible for scraping football match data.
"""
import requests
import time
from bs4 import BeautifulSoup
import datetime
import pandas as pd
from io import StringIO

class Scraper:
    """
    This is the parent Scraper class
    """
    main_url: str
    years: list[int]
    all_matches: list
    
    def __init__(self) -> None:
        """Initializer for Scraper"""
        self.main_url = "https://fbref.com"
        self.years = list(range(datetime.datetime.now().year, 2021, -1))
        self.all_matches = []


class MatchScraper(Scraper):
    """
    This is the child class of the Scraper class responsible for scrapping match data.
    """
    match_url: str

    def __init__(self) -> None:
        """Initializer for MatchScrapper"""
        # This is necessary to call the parent function's init method
        super().__init__()
        self.match_url = self.main_url + "/en/comps/9/Premier-League-Stats"

    def get_stats(self) -> None:
        """
        Method which is responsible for scraping the match stats and downloading CSV file into directory.
        """

        for year in self.years:
            data = requests.get(self.match_url)
            soup = BeautifulSoup(data.text, features="lxml")
            standings_table = soup.select('table.stats_table')[0]

            # Find the a tags in the HTML code
            links = [l.get("href") for l in standings_table.find_all('a')]
            links = [l for l in links if '/squads' in l]
            team_urls = [self.main_url + l for l in links]

            previous_season = soup.select("a.prev")[0].get("href")
            self.match_url = self.main_url + previous_season

            for team_url in team_urls:
                team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
                # Get the data for each team_url
                data = requests.get(team_url)
                print(data.status_code)
                matches = pd.read_html(StringIO(data.text), match="Scores & Fixtures")[0]

                soup = BeautifulSoup(data.text, features="lxml")
                links = [l.get("href") for l in soup.find_all('a')]
                links = [l for l in links if l and 'all_comps/shooting/' in l]

                # shooting_data = requests.get(self.main_url + links[0])
                # print(self.main_url + links[0])

                # shooting = pd.read_html(StringIO(shooting_data.text), match="Shooting")[0]
                # # Here we are removing the double indexed header and only keeper lower level since
                # # droplevel removes only the first level
                # shooting.columns = shooting.columns.droplevel()

                # try:
                #     team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PKatt"]], on="Date")
                # except ValueError:
                #     # We might get missing data or improper loads from the Fbref server calls and we handle them by not merging
                #     continue

                # Only keep the Premier League Data
                matches = matches[matches["Comp"] == "Premier League"]

                matches["Season"] = year
                matches["Team"] = team_name
                self.all_matches.append(matches)
                print(f"Done getting {team_name} stats from: {year}")
                time.sleep(5)
        
        match_df = pd.concat(self.all_matches)
        # Make the column names lower case for ease of use
        match_df.columns = [c.lower() for c in match_df.columns]

        match_df.to_csv("new_matches.csv")
        return None


        



class PlayerScraper(Scraper):
    """
    This is the child class of the Scraper class responsible for scrapping player data.
    """

    pass


if __name__ == "__main__":
    scraper = Scraper()
    match_scraper = MatchScraper()
    print(match_scraper.get_stats())