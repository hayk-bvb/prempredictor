"""
This file is responsible for housing the helper function rolling_averages for preds.py
"""

def rolling_averages(group, cols, new_cols, num_matches):
    """
    This function is responsible for 
    """
    # Here we want to sort by date to look at the last 3 matches the team has played
    group = group.sort_values("date")

    # We use closed='left' to indicate the method to not include the latest coloumn in the average. Similar to python list indexing [:3]
    rolling_stats = group[cols].rolling(num_matches, closed='left').mean()
    group[new_cols] = rolling_stats
    # Remove rows with missing values to avoid errors
    group = group.dropna(subset=new_cols)

    return group