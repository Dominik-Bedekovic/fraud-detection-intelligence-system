# Data

This folder is used for local dataset storage.

## Important

The dataset file is **not committed to Git** because it exceeds GitHub's file size limit.

## Dataset source

The dataset is downloaded automatically when running ml/train.py if not present.

If download fails: Download the dataset manually from Kaggle (https://www.kaggle.com/datasets/amanalisiddiqui/fraud-detection-dataset) and place it in this folder. Current expected file name:

`AIML Dataset.csv`

## Usage

Machine learning scripts will read the dataset from the `data/` folder during local execution.

## Note

If needed, the exact filename and parsing logic can be adjusted later in the ML scripts.