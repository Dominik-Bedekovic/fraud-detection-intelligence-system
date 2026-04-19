from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.features import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    FeatureSelector,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "backend" / "model"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "AIML Dataset.csv"
TARGET_COLUMN = "isFraud"


def build_preprocessor() -> ColumnTransformer:
    # Numeric features are imputed and scaled before model training.
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    # Categorical features are imputed and one-hot encoded so unseen values
    # at inference time do not break the pipeline.
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )


def build_pipeline(classifier) -> Pipeline:
    # The pipeline keeps feature engineering, preprocessing, and classification
    # together so training and inference use the exact same transformations.
    return Pipeline(
        steps=[
            ("feature_selector", FeatureSelector()),
            ("preprocessor", build_preprocessor()),
            ("classifier", classifier),
        ]
    )


def choose_threshold(y_true, probabilities) -> tuple[float, float]:
    # The decision threshold is selected from the validation set instead of
    # relying on the default 0.50, which is often suboptimal for imbalanced data.
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)

    best_threshold = 0.50
    best_f1 = -1.0

    for index, threshold in enumerate(thresholds):
        p = precision[index]
        r = recall[index]
        if p + r == 0:
            continue
        f1 = 2 * p * r / (p + r)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = float(threshold)

    # Clamp the threshold to a practical range to avoid extreme values.
    best_threshold = max(0.05, min(best_threshold, 0.80))
    return best_threshold, best_f1


def evaluate_at_threshold(name, y_true, probabilities, threshold: float) -> dict:
    # Final test evaluation is done with the chosen validation threshold to
    # reflect the actual decision rule used by the backend.
    y_pred = (probabilities >= threshold).astype(int)

    print(f"\n{name} - threshold: {threshold:.4f}")
    print("\nConfusion matrix:")
    print(confusion_matrix(y_true, y_pred))

    print("\nClassification report:")
    print(classification_report(y_true, y_pred, digits=4))

    roc_auc = roc_auc_score(y_true, probabilities)
    pr_auc = average_precision_score(y_true, probabilities)

    print(f"ROC AUC: {roc_auc:.6f}")
    print(f"PR AUC : {pr_auc:.6f}")

    report = classification_report(y_true, y_pred, digits=4, output_dict=True)
    fraud_metrics = report["1"]

    return {
        "precision": float(fraud_metrics["precision"]),
        "recall": float(fraud_metrics["recall"]),
        "f1_score": float(fraud_metrics["f1-score"]),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "support": int(fraud_metrics["support"]),
    }


def load_dataset() -> pd.DataFrame:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset")

    return df


def main():
    print(f"Loading dataset from: {DATA_FILE}")
    df = load_dataset()

    # Remove columns that are not used as model inputs, if present in the dataset.
    drop_columns = [col for col in ["nameOrig", "nameDest", "isFlaggedFraud"] if col in df.columns]

    if len(df) > 1_000_000:
        print("Dataset is large. Using a stratified sample of 1,000,000 rows for Alpha checkpoint iteration.")

        sample_size = 1_000_000
        if sample_size < len(df):
            # Downsampling keeps Alpha checkpoint training practical while preserving class balance.
            df, _ = train_test_split(
                df,
                train_size=sample_size,
                stratify=df[TARGET_COLUMN],
                random_state=42,
            )

        df = df.reset_index(drop=True)

    X = df.drop(columns=[TARGET_COLUMN] + drop_columns)
    y = df[TARGET_COLUMN].astype(int)

    # Split into train / validation / test to keep model selection separate
    # from the final unbiased evaluation.
    X_train, X_temp, y_train, y_temp = train_test_split(
        X,
        y,
        test_size=0.30,
        stratify=y,
        random_state=42,
    )

    X_valid, X_test, y_valid, y_test = train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        stratify=y_temp,
        random_state=42,
    )

    # A small baseline model set is enough for Alpha checkpoint comparison.
    candidate_models = {
        "logistic_regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=42,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced_subsample",
            min_samples_leaf=2,
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced_subsample",
            min_samples_leaf=2,
        ),
    }

    best_name = None
    best_pipeline = None
    best_threshold = None
    best_score = -1.0

    print("Training candidate models...")

    for name, classifier in candidate_models.items():
        print(f"\n{'=' * 70}")
        print(f"Model: {name}")

        pipeline = build_pipeline(classifier)
        pipeline.fit(X_train, y_train)

        valid_probabilities = pipeline.predict_proba(X_valid)[:, 1]
        pr_auc = average_precision_score(y_valid, valid_probabilities)
        threshold, best_f1 = choose_threshold(y_valid, valid_probabilities)

        print(f"Validation ROC AUC: {roc_auc_score(y_valid, valid_probabilities):.6f}")
        print(f"Validation PR AUC : {pr_auc:.6f}")
        print(f"Validation best F1: {best_f1:.6f}")
        print(f"Chosen threshold  : {threshold:.6f}")

        # PR AUC is the primary selection metric because fraud detection is
        # heavily imbalanced and ROC AUC can look overly optimistic.
        if pr_auc > best_score:
            best_score = pr_auc
            best_name = name
            best_pipeline = pipeline
            best_threshold = threshold

    print(f"\n{'=' * 70}")
    print(f"Best model on validation PR AUC: {best_name}")
    print(f"Chosen threshold: {best_threshold:.6f}")

    print("\nRetraining best model on train + validation data...")
    X_train_valid = pd.concat([X_train, X_valid], axis=0)
    y_train_valid = pd.concat([y_train, y_valid], axis=0)
    best_pipeline.fit(X_train_valid, y_train_valid)

    test_probabilities = best_pipeline.predict_proba(X_test)[:, 1]
    test_metrics = evaluate_at_threshold(
        best_name,
        y_test,
        test_probabilities,
        best_threshold,
    )

    # Store both the trained pipeline and metadata needed by the backend.
    model_bundle = {
        "pipeline": best_pipeline,
        "threshold": float(best_threshold),
        "model_name": best_name,
        "metrics": test_metrics,
        "features_version": "paysim_kt1_v1",
    }

    model_path = MODEL_DIR / "fraud_pipeline.joblib"
    joblib.dump(model_bundle, model_path)

    print(f"\nModel saved to: {model_path}")


if __name__ == "__main__":
    main()