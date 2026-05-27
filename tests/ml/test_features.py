import numpy as np
import pandas as pd
import pytest

from ml.features import FeatureSelector, MODEL_FEATURES


def test_feature_selector_returns_expected_feature_columns():
    raw_data = pd.DataFrame(
        [
            {
                "step": 1,
                "type": "transfer",
                "amount": 1000,
                "oldbalanceOrg": 1000,
                "newbalanceOrig": 0,
                "oldbalanceDest": 0,
                "newbalanceDest": 0,
            }
        ]
    )

    result = FeatureSelector().transform(raw_data)

    assert list(result.columns) == MODEL_FEATURES


def test_feature_selector_normalizes_type_and_creates_derived_features():
    raw_data = pd.DataFrame(
        [
            {
                "step": 1,
                "type": "transfer",
                "amount": 1000,
                "oldbalanceOrg": 1000,
                "newbalanceOrig": 0,
                "oldbalanceDest": 200,
                "newbalanceDest": 1200,
            }
        ]
    )

    result = FeatureSelector().transform(raw_data)

    assert result.loc[0, "type"] == "TRANSFER"
    assert result.loc[0, "amount_log"] == pytest.approx(np.log1p(1000))
    assert result.loc[0, "orig_balance_delta"] == 1000
    assert result.loc[0, "dest_balance_delta"] == 1000
    assert result.loc[0, "orig_zero_balance"] == 0
    assert result.loc[0, "dest_zero_balance"] == 0
    assert result.loc[0, "amount_to_oldbalance_ratio"] == 1


def test_feature_selector_adds_missing_required_columns():
    raw_data = pd.DataFrame(
        [
            {
                "amount": 250,
            }
        ]
    )

    result = FeatureSelector().transform(raw_data)

    assert result.loc[0, "type"] == "UNKNOWN"
    assert result.loc[0, "step"] == 0
    assert result.loc[0, "amount"] == 250
    assert result.loc[0, "oldbalanceOrg"] == 0
    assert result.loc[0, "newbalanceOrig"] == 0
    assert result.loc[0, "oldbalanceDest"] == 0
    assert result.loc[0, "newbalanceDest"] == 0


def test_feature_selector_converts_invalid_numeric_values_and_clips_negative_values():
    raw_data = pd.DataFrame(
        [
            {
                "step": -5,
                "type": "PAYMENT",
                "amount": -100,
                "oldbalanceOrg": "invalid",
                "newbalanceOrig": -1,
                "oldbalanceDest": None,
                "newbalanceDest": 50,
            }
        ]
    )

    result = FeatureSelector().transform(raw_data)

    assert result.loc[0, "step"] == 0
    assert result.loc[0, "amount"] == 0
    assert result.loc[0, "oldbalanceOrg"] == 0
    assert result.loc[0, "newbalanceOrig"] == 0
    assert result.loc[0, "oldbalanceDest"] == 0
    assert result.loc[0, "newbalanceDest"] == 50


def test_feature_selector_handles_zero_old_balance_ratio_safely():
    raw_data = pd.DataFrame(
        [
            {
                "step": 1,
                "type": "TRANSFER",
                "amount": 100,
                "oldbalanceOrg": 0,
                "newbalanceOrig": 0,
                "oldbalanceDest": 0,
                "newbalanceDest": 0,
            }
        ]
    )

    result = FeatureSelector().transform(raw_data)

    assert np.isfinite(result.loc[0, "amount_to_oldbalance_ratio"])
    assert result.loc[0, "amount_to_oldbalance_ratio"] == 100


def test_feature_selector_does_not_mutate_original_dataframe():
    raw_data = pd.DataFrame(
        [
            {
                "step": 1,
                "type": "CASH_OUT",
                "amount": 500,
                "oldbalanceOrg": 500,
                "newbalanceOrig": 0,
                "oldbalanceDest": 0,
                "newbalanceDest": 0,
            }
        ]
    )

    FeatureSelector().transform(raw_data)

    assert "amount_log" not in raw_data.columns
    assert "orig_balance_delta" not in raw_data.columns
    assert "dest_balance_delta" not in raw_data.columns