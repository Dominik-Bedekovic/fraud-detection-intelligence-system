# Machine Learning

This folder contains the machine learning part of the project.

## Responsibilities

The ML layer is responsible for:

- dataset inspection
- feature preparation
- model training
- model evaluation
- model export for backend usage

## Planned files

- `features.py` — feature selection and transformations
- `train.py` — baseline training pipeline
- `evaluate.py` — evaluation utilities or separate experiments

## Alpha scope

For the first control point, the goal is to produce:

- a first baseline model
- basic preprocessing logic
- evaluation output
- an exported model bundle for backend integration

## Current Alpha checkpoint baseline

The current Alpha checkpoint baseline uses transaction-level financial features derived from the selected fraud dataset.

### Input features

- `step`
- `type`
- `amount`
- `oldbalanceOrg`
- `newbalanceOrig`
- `oldbalanceDest`
- `newbalanceDest`

### Derived features

- `amount_log`
- `orig_balance_delta`
- `dest_balance_delta`
- `orig_zero_balance`
- `dest_zero_balance`
- `amount_to_oldbalance_ratio`

### Candidate models

- Logistic Regression
- Random Forest
- Extra Trees

### Selected baseline model

- Random Forest

Detailed metrics are documented in the project documentation files.