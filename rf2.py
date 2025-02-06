import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import numpy as np
from mapping import MissingDict, map_values

# Load your datasets
data_part1 = pd.read_csv('matches.csv')
data_part2 = pd.read_csv('scraping/merged_output.csv')

# Combine the datasets by aligning columns (add missing features with NaN where necessary)
combined_data = pd.concat(
    [data_part1.reindex(columns=data_part2.columns, fill_value=np.nan), data_part2], ignore_index=True
)

combined_data = data_part2

# Preprocess combined data (convert date, time, venue, and opponent to categories)
combined_data["date"] = pd.to_datetime(combined_data["date"])
combined_data["venue_code"] = combined_data["venue"].astype("category").cat.codes
combined_data["opp_code"] = combined_data["opponent"].astype("category").cat.codes
combined_data["ref_code"] = combined_data["referee"].astype("category").cat.codes
combined_data["hour"] = combined_data["time"].str.replace(":.+", "", regex=True).astype("int")
combined_data["day_code"] = combined_data["date"].dt.day_of_week
combined_data["target"] = (combined_data["result"] == "W").astype("int")

# Handle missing values (fill NaNs with 0 for numerical features, as an example)
combined_data.fillna(0, inplace=True)

# Define predictors based on both datasets
predictors = ["venue_code", "ref_code", "opp_code", "hour", "day_code", "g/sh", "npxg", "g-xg", "np:g-xg"]

# Sort the data by date to ensure chronological order
combined_data = combined_data.sort_values("date", ascending=[False])

# Define the columns for which we want rolling averages
stats_columns = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt", "g/sh", "npxg", "g-xg", "np:g-xg"]

# Group by team and calculate rolling averages for past k games
k = 3  # Adjust this value as needed
combined_data = combined_data.groupby("team").apply(
    lambda df: df.sort_values("date").assign(**{f"{col}_rolling": df[col].rolling(k, min_periods=1).mean() for col in stats_columns}).assign(team=df.name),
    include_groups=False
)

# Drop extra team index level for ease of use and also apply full length index to DF, aligned with .shape[0]
combined_data = combined_data.droplevel('team')
combined_data.index = range(combined_data.shape[0])

# Ensure the final dataset is still sorted in descending order
combined_data = combined_data.sort_values("date", ascending=False)

# Handle missing values introduced by rolling averages
combined_data.fillna(0, inplace=True)

# Split the data chronologically (80% for training, 20% for testing)
split_index = int(0.8 * len(combined_data))
train_data = combined_data.iloc[split_index:]
test_data = combined_data.iloc[:split_index]

# Initialize and train the RandomForest model
rf_model = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)
rf_model.fit(train_data[predictors], train_data["target"])

# Evaluate the model
predictions = rf_model.predict(test_data[predictors])
accuracy = accuracy_score(test_data["target"], predictions)

# Extract feature importances
feature_importances = rf_model.feature_importances_


# Make predictions for the entire dataset
combined_data["predicted"] = rf_model.predict(combined_data[predictors])

# Normalize team names as intended
mapping = MissingDict(**map_values)
combined_data["new_team"] = combined_data["team"].map(mapping)


# Merge the DataFrame with itself to compare predictions from both teams' perspectives
merged = combined_data.merge(
    combined_data, 
    left_on=["date", "new_team"], 
    right_on=["date", "opponent"], 
    suffixes=('_x', '_y')
)


# Calculate precision based on merged predictions
precision_v2 = merged[(merged["predicted_x"] == 1) & (merged["predicted_y"] == 0)]["target_x"].value_counts()

# Display results
print(f"Model Accuracy: {accuracy:.2%}")
print("Feature Importances:")
for feature, importance in zip(predictors, feature_importances):
    print(f"{feature}: {importance:.2%}")

print(f"Here is our model's precision: {precision_v2}")


