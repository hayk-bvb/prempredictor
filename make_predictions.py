"""
This file will be used to store the make_predictions helper function for preds.py
"""
import pandas as pd
from sklearn.metrics import precision_score


def make_predictions(rf, data, predictors):
    """
    """
    # Need to separate data such that we use older data to predict future match results
    train = data[data["date"] < '2023-06-01']
    test = data[data["date"] > '2023-09-01']

    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])

    combined = pd.DataFrame(dict(actual=test["target"], predicted=preds), index=test.index)
    # Find precision score
    precision = precision_score(test["target"], preds)

    return combined, precision


