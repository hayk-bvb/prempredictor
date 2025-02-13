"""
This file is responsible for storing the class MissingDict to deal with missing values within our DF
"""

class MissingDict(dict):
    __missing__ = lambda self, key: key

# Dictionary of full length team names that will be shortened for ease-of-use
map_values = {
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcastle United": "Newcastle Utd",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
    "Leeds United": "Leeds Utd",
}