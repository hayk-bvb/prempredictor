import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from rolling_averages import rolling_averages
from make_predictions import make_predictions
from mapping import MissingDict, map_values

matches = pd.read_csv("scraping/merged_output.csv")

# First lets clean up some of our data and convert to float64
matches["date"] = pd.to_datetime(matches["date"])

# Create predictors for the ML model
# Here we convert venue from "Home" and "Away" to a category and then converting that category into numbers with .cat.codes
matches["venue_code"] = matches["venue"].astype("category").cat.codes
# Do the same with referees
matches["ref_code"] = matches["referee"].astype("category").cat.codes

matches["opp_code"] = matches["opponent"].astype("category").cat.codes
# Remove the coloumn and minutes ("16:30") and keep the whole hour with regex, converted to int so that we can inlcude in ML model
matches["hour"] = matches["time"].str.replace(":.+", "", regex=True).astype("int")

# Assign predictor for the different days of the week, same reason as above
matches["day_code"] = matches["date"].dt.day_of_week

# Assign target
matches["target"] = (matches["result"] == "W").astype("int")


# Initialize RandomForrest
rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)


predictors = ["venue_code", "opp_code", "hour", "day_code", "ref_code"]


cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt", "g/sh", "npxg", "g-xg", "np:g-xg"]
new_cols = [f"{c}_rolling" for c in cols]

# Create a DF for every squad in our data with rolling averages of past 5 games
matches_rolling = matches.groupby("team").apply(
    lambda x: rolling_averages(x, cols, new_cols, 2).assign(team=x.name), include_groups=False
)
# Drop extra team index level for ease of use and also apply full length index to DF, aligned with .shape[0]
matches_rolling = matches_rolling.droplevel('team')
matches_rolling.index = range(matches_rolling.shape[0])


combined, precision = make_predictions(rf, matches_rolling, predictors + new_cols)

# Include the date, team, opponent and result with the actual and predicted for easier debugging
combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index=True, right_index=True)

# Lets normalize the team names
mapping = MissingDict(**map_values)
combined["new_team"] = combined["team"].map(mapping)

# Merge DF with itself to inspect both sides of a match
merged = combined.merge(combined, left_on=["date", "new_team"], right_on=["date", "opponent"])

# Lets look at when the model predicted team A would win and team B would lose, what actually happened
precision_v2 = merged[(merged["predicted_x"] == 1) & (merged['predicted_y'] == 0)]["actual_x"].value_counts()


if __name__ == "__main__":
    # print(matches["team"].value_counts())
    print(precision)
    # print(combined)
    # print(merged)
    print(precision_v2)