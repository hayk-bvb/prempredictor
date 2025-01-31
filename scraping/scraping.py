"""
This file contains the class responsible for scraping football match data.
"""
import requests
import time
from bs4 import BeautifulSoup
import datetime
import pandas as pd
from io import StringIO
import random

def load_proxies_from_csv(file_path):
    """Load proxies from the CSV file."""
    df = pd.read_csv(file_path)
    return df['proxy'].tolist()

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
        self.proxies_file_path = "proxies.csv"
        self.proxies = load_proxies_from_csv(self.proxies_file_path)

    def get_with_proxies(self, url, proxies, max_retries=5, backoff_factor=1):
        """
        Make a request to a URL using random proxies to bypass 429 errors.
        
        Parameters:
            url (str): The URL to make the request to.
            proxies (list): A list of proxy servers in the format 'http://proxy:port'.
            max_retries (int): Maximum number of retries on failure (default 5).
            backoff_factor (float): Multiplier for exponential backoff between retries (default 1).
            
        Returns:
            Response: The `requests` Response object if the request is successful.
        """
        for attempt in range(max_retries):
            try:
                # Randomly select a proxy from the list
                proxy = random.choice(proxies)
                proxy_dict = {"http": proxy}

                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Safari/605.1.15",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
                ]

                headers = {"User-Agent": random.choice(user_agents)}
                response = requests.get(url, proxies=proxy_dict, headers=headers, timeout=10)



                # If the request is successful and not a 429 error, return the response
                if response.status_code != 429:
                    return response

                # Handle 429 by waiting before retrying
                print(f"429 error received. Retrying in {backoff_factor * (2 ** attempt)} seconds...")
                time.sleep(backoff_factor * (2 ** attempt))

            except requests.RequestException as e:
                print(f"Request failed: {e}")

        raise Exception("Max retries exceeded. Could not get a successful response.")



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
        self.cache = {self.match_url: None}

    # def populate_cache(self, url) -> None:
    #     self.cache[url] = requests.get(url).text

    def get_shooting_stats(self) -> None:
        # self.populate_cache(self.match_url)

        for year in self.years:
            # If the cache is empty
            if not self.cache[self.match_url]:
                data = self.get_with_proxies(self.match_url, self.proxies)
            else:
                data = self.cache[self.match_url]

            soup = BeautifulSoup(data.text, features="lxml")
            standings_table = soup.select('table.stats_table')[0]

            # Find the a tags in the HTML code
            links = [l.get("href") for l in standings_table.find_all('a')]
            links = [l for l in links if '/squads' in l]
            team_urls = [self.main_url + l for l in links]

            # Assign variable for previous season        
            previous_season = soup.select("a.prev")[0].get("href")
            self.match_url = self.main_url + previous_season

            for team_url in team_urls:
                team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
                

                team_data = self.get_with_proxies(team_url, self.proxies)
                print(team_data.status_code)


                soup = BeautifulSoup(team_data.text, features="lxml")
                links = [l.get("href") for l in soup.find_all('a')]
                links = [l for l in links if l and 'all_comps/shooting/' in l]

                shooting_data = self.get_with_proxies(self.main_url + links[0], self.proxies)

                shooting = pd.read_html(StringIO(shooting_data.text), match="Shooting")[0]

                shooting.columns = shooting.columns.droplevel()

                shooting["Season"] = year
                shooting["Team"] = team_name
                self.all_matches.append(shooting)
                print(f"Done getting shooting stats{team_name} stats from: {year}")
                time.sleep(3)
        
        shooting_df = pd.concat(self.all_matches)
        # Make the column names lower case for ease of use
        shooting_df.columns = [c.lower() for c in shooting_df.columns]

        shooting_df.to_csv("shooting.csv")
        return None



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

                shooting_data = requests.get(self.main_url + links[0])
                print(self.main_url + links[0])

                shooting = pd.read_html(StringIO(shooting_data.text), match="Shooting")[0]
                # Here we are removing the double indexed header and only keeper lower level since
                # droplevel removes only the first level
                shooting.columns = shooting.columns.droplevel()

                try:
                    team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PKatt"]], on="Date")
                except ValueError:
                    # We might get missing data or improper loads from the Fbref server calls and we handle them by not merging
                    continue

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
    
    def clean_future_data(self, file) -> None:
        """
        Remove chunks of data which are H2H rows of matches which will take place in the future.
        Saves .csv file to local directory
        """

        # Read the old unfiltered file and set the "date" column to be a datetime value
        df = pd.read_csv(file)
        df["date"] = pd.to_datetime(df["date"])

        # Make a copy of the old df
        new_df = df.copy()
        # Set a variable for today's date
        today = datetime.datetime.today().date()

        # Filter the new_df to only inlclude rows that are from today
        filtered = new_df[new_df["date"] < pd.Timestamp(today)]
        filtered.to_csv("new_matches_modified.csv", index=True)

        return




class PlayerScraper(Scraper):
    """
    This is the child class of the Scraper class responsible for scrapping player data.
    """

    pass


if __name__ == "__main__":
    scraper = Scraper()
    match_scraper = MatchScraper()
    match_scraper.get_shooting_stats()
    # match_scraper.clean_future_data("new_matches.csv")