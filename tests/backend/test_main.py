from fastapi.testclient import TestClient

from backend.app import models as db_models
from backend.app.main import app, get_db, prediction_service


class FakeDB:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.executed = []
        self._next_id = 1

    def execute(self, statement):
        self.executed.append(statement)
        return 1

    def add(self, item):
        if getattr(item, "id", None) is None:
            item.id = self._next_id
            self._next_id += 1

        self.added.append(item)

    def commit(self):
        self.commits += 1

    def refresh(self, item):
        if getattr(item, "id", None) is None:
            item.id = self._next_id
            self._next_id += 1


def create_test_client(fake_db: FakeDB) -> TestClient:
    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_database_health_returns_connected():
    fake_db = FakeDB()
    client = create_test_client(fake_db)

    response = client.get("/db/health")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"database": "connected"}
    assert len(fake_db.executed) == 1


def test_predict_returns_result_and_stores_transaction_and_prediction(monkeypatch):
    fake_db = FakeDB()
    client = create_test_client(fake_db)

    monkeypatch.setattr(
        prediction_service,
        "predict_fraud",
        lambda transaction_data: {
            "fraud_probability": 98.5,
            "is_fraud": True,
        },
    )

    payload = {
        "type": "TRANSFER",
        "amount": 5000,
        "oldbalanceOrg": 5000,
        "newbalanceOrig": 0,
        "oldbalanceDest": 0,
        "newbalanceDest": 0,
    }

    response = client.post("/predict", json=payload)

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "prediction": 1,
        "label": "fraud",
        "probability": 98.5,
    }

    assert fake_db.commits == 2
    assert len(fake_db.added) == 2

    stored_transaction = fake_db.added[0]
    stored_prediction = fake_db.added[1]

    assert isinstance(stored_transaction, db_models.Transaction)
    assert stored_transaction.type == "TRANSFER"
    assert stored_transaction.amount == 5000
    assert stored_transaction.source == "single"
    assert stored_transaction.step == 1

    assert isinstance(stored_prediction, db_models.PredictionResult)
    assert stored_prediction.transaction_id == stored_transaction.id
    assert stored_prediction.prediction == 1
    assert stored_prediction.label == "fraud"
    assert stored_prediction.probability == 98.5


def test_predict_batch_returns_results_and_stores_batch_transactions(monkeypatch):
    fake_db = FakeDB()
    client = create_test_client(fake_db)

    monkeypatch.setattr(
        prediction_service,
        "predict_fraud_batch",
        lambda dataframe: [
            {
                "fraud_probability": 95.0,
                "is_fraud": True,
            },
            {
                "fraud_probability": 2.5,
                "is_fraud": False,
            },
        ],
    )

    csv_content = (
        "step,type,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest\n"
        "1,TRANSFER,5000,5000,0,0,0\n"
        "1,PAYMENT,50,1000,950,0,0\n"
    )

    response = client.post(
        "/predict/batch",
        files={
            "file": (
                "transactions.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "results": [
            {
                "prediction": 1,
                "label": "fraud",
                "probability": 95.0,
            },
            {
                "prediction": 0,
                "label": "not_fraud",
                "probability": 2.5,
            },
        ]
    }

    stored_transactions = [
        item for item in fake_db.added if isinstance(item, db_models.Transaction)
    ]
    stored_predictions = [
        item for item in fake_db.added if isinstance(item, db_models.PredictionResult)
    ]

    assert fake_db.commits == 2
    assert len(stored_transactions) == 2
    assert len(stored_predictions) == 2

    assert stored_transactions[0].source == "batch"
    assert stored_transactions[0].type == "TRANSFER"
    assert stored_transactions[1].source == "batch"
    assert stored_transactions[1].type == "PAYMENT"

    assert stored_predictions[0].transaction_id == stored_transactions[0].id
    assert stored_predictions[0].label == "fraud"

    assert stored_predictions[1].transaction_id == stored_transactions[1].id
    assert stored_predictions[1].label == "not_fraud"


def test_predict_batch_rejects_non_csv_file():
    fake_db = FakeDB()
    client = create_test_client(fake_db)

    response = client.post(
        "/predict/batch",
        files={
            "file": (
                "transactions.txt",
                "not,a,csv",
                "text/plain",
            )
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Invalid file format. Please upload a CSV file."
    }