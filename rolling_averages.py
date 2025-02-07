"""
This file is responsible for housing the helper function rolling_averages for preds.py
"""

import pandas as pd

def add_rolling_averages(df, stats_columns, k=7):
    """
    Adds rolling averages to the DataFrame for the specified columns over the past k games.
    
    Parameters:
        df (pd.DataFrame): The input DataFrame. Must contain 'team' and 'date' columns.
        stats_columns (list): List of columns to compute rolling averages for.
        k (int): The number of past games to consider for the rolling average.
        
    Returns:
        pd.DataFrame: The DataFrame with rolling averages added.
    """
    # Ensure the date column is in datetime format for sorting
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    # Group by team and apply rolling averages
    df_with_rolling = (
        df.groupby("team").apply(
            lambda group: group.sort_values("date").assign(
                **{f"{col}_rolling": group[col].rolling(k, min_periods=1).mean() for col in stats_columns}
            )
        )
    )

    # Reset the index to match the original DataFrame format
    return df_with_rolling.reset_index(drop=True)