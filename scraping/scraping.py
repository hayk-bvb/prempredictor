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


class Scraper:
    """This is the parent Scraper class"""
    main_url: str
    years: list[int]
    all_matches: list
    
    def __init__(self) -> None:
        """Initializer for Scraper"""
        self.main_url = "https://fbref.com"
        self.years = list(range(datetime.datetime.now().year, 2021, -1))
        self.all_matches = []

    def get_request(self, url, max_retries=100, backoff_factor=1):
        """
        Make a request to a URL, handles 429 errors.
        
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
                response = requests.get(url, timeout=10)

                # If the request is successful and not a 429 error, return the response
                if response.status_code != 429:
                    return response

                # Handle 429 by waiting before retrying
                print(f"429 error received. Retrying in {backoff_factor * (2 ** attempt)} seconds...")
                time.sleep(backoff_factor * (2 ** attempt))

            except requests.RequestException as e:
                print(f"Request failed: {e}")

        raise Exception("Max retries exceeded. Could not get a successful response.")
    
    def print_df(self, filename) -> None:
        """Helper function which prints out the CSV as a Pandas DF."""

        df = pd.read_csv(filename)
        return df



class MatchScraper(Scraper):
    """This is the child class of the Scraper class responsible for scrapping match data."""
    match_url: str

    def __init__(self) -> None:
        """Initializer for MatchScrapper"""
        # This is necessary to call the parent function's init method
        super().__init__()
        self.match_url = self.main_url + "/en/comps/9/Premier-League-Stats"
        self.cache = {self.match_url: None}


    def get_shooting_stats(self) -> None:

        try:
            for year in self.years:                
                data = self.get_request(self.match_url)

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
                    print(team_url)
                    team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
                    

                    team_data = self.get_request(team_url)
                    print(team_data.status_code)


                    soup = BeautifulSoup(team_data.text, features="lxml")
                    links = [l.get("href") for l in soup.find_all('a')]
                    links = [l for l in links if l and 'all_comps/shooting/' in l]

                    team_shooting_link = self.main_url + links[0]

                    # Open file with team log
                    with open('shooting_stats_team_log.txt', 'r') as f:
                        team_log = [line.strip() for line in f.readlines()]

                    if team_name + "#" + str(year) not in team_log:
                        shooting_data = self.get_request(team_shooting_link)

                    else:
                        # Go to next team
                        continue

                    shooting = pd.read_html(StringIO(shooting_data.text), match="Shooting")[0]

                    shooting.columns = shooting.columns.droplevel()

                    shooting["Season"] = year
                    shooting["Team"] = team_name
                    self.all_matches.append(shooting)
                    print(f"Done getting shooting stats {team_name} from: {year}")
                    with open("shooting_stats_team_log.txt", "a") as f:
                        f.write(f"{team_name}#{year}\n")
                    time.sleep(3)
            
            shooting_df = pd.concat(self.all_matches)
            # Make the column names lower case for ease of use
            shooting_df.columns = [c.lower() for c in shooting_df.columns]

            shooting_df.to_csv("shooting.csv")
            # If we get a max retries error, then we can log our progress
        except KeyboardInterrupt:
            shooting_df = pd.concat(self.all_matches)
            # Make the column names lower case for ease of use
            shooting_df.columns = [c.lower() for c in shooting_df.columns]
            shooting_df.to_csv("shooting.csv")
        return None



    def get_stats(self) -> None:
        """Method which is responsible for scraping the match stats and downloading CSV file into directory."""

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
    
    def clean_future_data(self, filename, exact_date=None) -> None:
        """Remove chunks of data which are H2H rows of matches which will take place in the future.
        Saves .csv file to local directory"""

        # Read the old unfiltered file and set the "date" column to be a datetime value
        df = pd.read_csv(filename)
        df["date"] = pd.to_datetime(df["date"])

        # Make a copy of the old df
        new_df = df.copy()
        if exact_date:
            date_string = exact_date
            today = datetime.datetime.strptime(date_string, "%Y-%m-%d")
        else:
            # Set a variable for today's date
            today = datetime.datetime.today().date()


        # Filter the new_df to only inlclude rows that are from today
        filtered = new_df[new_df["date"] < pd.Timestamp(today)]
        # Only keep Premier League games
        filtered = filtered[filtered["comp"] == "Premier League"]
        filtered.to_csv(f"{filename.split(".")[0]}_modified.csv", index=True)
        return
    
    def concat_CSVs(self, filename1, filename2, new_filename) -> None:
        """A helper function used to combine CSVs together and save to another CSV."""
        if new_filename[-4:] != ".csv":
            raise Exception("Please enter correct filename ending with .csv")

        # Read the two CSV files
        df1 = pd.read_csv(filename1)
        df2 = pd.read_csv(filename2)

        # Concatenate the DataFrames, placing df1 data before df2
        combined_df = pd.concat([df1, df2], ignore_index=True)

        # Save the combined DataFrame to a new CSV file
        combined_df.to_csv(f"{new_filename}", index=True)

    def delete_column(self, filename, col_num, new_filename) -> None:
        """Helper function used to delete a column from a CSV and then save it to a new CSV."""
        if new_filename[-4:] != ".csv":
            raise Exception("Please enter correct filename ending with .csv")
        
        df = pd.read_csv(filename)
        first_column = df.columns[col_num]
        # Delete first
        df = df.drop([first_column], axis=1)
        df.to_csv(f'{new_filename}', index=False)
        return
    
    def merge_CSVs(self, filename1: str, filename2: str, how="inner") -> None:
        """Helper function used to merge CSVs together and then save it to new CSV file."""

        df1 = pd.read_csv(filename1)
        df2 = pd.read_csv(filename2)

        # Get the common columns between both CSVs
        common_columns = list(set(df1.columns) & set(df2.columns))

        # Merge only on the common columns without suffixes
        merged_df = pd.merge(df1, df2, on=common_columns, how=how, suffixes=('', ''))

        # Output the merged DataFrame to a new CSV
        merged_df.to_csv("merged_output.csv", index=False)

        # Save the merged DataFrame to a new CSV
        merged_df.to_csv("merged_output.csv", index=False)
        return


class PlayerScraper(Scraper):
    """This is the child class of the Scraper class responsible for scrapping player data.
    
    COMING SOON
    """

    pass


if __name__ == "__main__":
    scraper = Scraper()
    match_scraper = MatchScraper()
    # match_scraper.get_shooting_stats()
    # match_scraper.clean_future_data("shooting_final.csv", "2025-01-26")

    # match_scraper.concat_CSVs("temp_modified.csv", "shooting_modified.csv", "shooting_final.csv")
    # match_scraper.delete_column("new_matches_modified.csv", 0, "new_matches_modified_NEW.csv")
    # print(match_scraper.print_df("new_matches_modified.csv"))
    match_scraper.merge_CSVs("new_matches_modified.csv", "shooting_final.csv", ["date", "time", "team", "opponent"])