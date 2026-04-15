from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

RAW_REQUIRED_COLUMNS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]

CATEGORICAL_FEATURES = [
    "type",
]

NUMERIC_FEATURES = [
    "step",
    "amount",
    "amount_log",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "orig_balance_delta",
    "dest_balance_delta",
    "orig_zero_balance",
    "dest_zero_balance",
    "amount_to_oldbalance_ratio",
]

MODEL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


class FeatureSelector(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()

        for column in RAW_REQUIRED_COLUMNS:
            if column not in df.columns:
                if column == "type":
                    df[column] = "UNKNOWN"
                else:
                    df[column] = 0

        df["type"] = df["type"].astype(str).fillna("UNKNOWN").str.upper()

        numeric_columns = [
            "step",
            "amount",
            "oldbalanceOrg",
            "newbalanceOrig",
            "oldbalanceDest",
            "newbalanceDest",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

        df["step"] = df["step"].fillna(0).clip(lower=0)
        df["amount"] = df["amount"].fillna(0.0).clip(lower=0.0)
        df["oldbalanceOrg"] = df["oldbalanceOrg"].fillna(0.0).clip(lower=0.0)
        df["newbalanceOrig"] = df["newbalanceOrig"].fillna(0.0).clip(lower=0.0)
        df["oldbalanceDest"] = df["oldbalanceDest"].fillna(0.0).clip(lower=0.0)
        df["newbalanceDest"] = df["newbalanceDest"].fillna(0.0).clip(lower=0.0)

        df["amount_log"] = np.log1p(df["amount"])

        df["orig_balance_delta"] = df["oldbalanceOrg"] - df["newbalanceOrig"]
        df["dest_balance_delta"] = df["newbalanceDest"] - df["oldbalanceDest"]

        df["orig_zero_balance"] = (df["oldbalanceOrg"] == 0).astype(int)
        df["dest_zero_balance"] = (df["oldbalanceDest"] == 0).astype(int)

        ratio_denominator = df["oldbalanceOrg"].replace(0, 1.0)
        df["amount_to_oldbalance_ratio"] = df["amount"] / ratio_denominator
        df["amount_to_oldbalance_ratio"] = np.nan_to_num(
            df["amount_to_oldbalance_ratio"],
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        return df[MODEL_FEATURES]