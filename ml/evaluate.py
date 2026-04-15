from __future__ import annotations

from pathlib import Path

import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "backend" / "model" / "fraud_pipeline.joblib"


def main():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    bundle = joblib.load(MODEL_PATH)

    print("Loaded model bundle")
    print(f"Model name: {bundle.get('model_name')}")
    print(f"Threshold : {bundle.get('threshold')}")
    print(f"Version   : {bundle.get('features_version')}")

    metrics = bundle.get("metrics", {})
    if metrics:
        print("\nStored test metrics:")
        for key, value in metrics.items():
            print(f"- {key}: {value}")
    else:
        print("\nNo metrics found in bundle.")


if __name__ == "__main__":
    main()