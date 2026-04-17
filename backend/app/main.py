from pathlib import Path


from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import pandas as pd
import joblib
from pydantic import BaseModel

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
import sys
sys.path.append(str(PROJECT_ROOT))

#pydantic validates incoming JSON and returns 422 on invalid input
class Transaction(BaseModel):
    step: int
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

#loads trained fraud model once during application startup
class ModelLoader:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.pipeline = None
        self.threshold = 0.1
        self.load_model()

    def load_model(self):
        try:
            bundle = joblib.load(self.model_path)
            #dict bundle with pipeline+threshold
            if isinstance(bundle,dict):  
                self.pipeline = bundle["pipeline"]
                self.threshold = bundle["threshold"]
            else:
                self.pipeline = bundle
        except Exception as e:
            print(f"error loading model: {e}")


#predict fraud probabilty for one transaction
    def predict(self, data: dict) -> float:
        if self.pipeline is None:
            raise ValueError("model not loaded")
        df = pd.DataFrame([data])
        return self.pipeline.predict_proba(df)[0][1]

#converts probability into fraud/not fraud
class PredictionService:
    def __init__(self, loader: ModelLoader):
        self.loader = loader

    def predict_fraud(self, transaction_data: dict) -> dict:
        probability = self.loader.predict(transaction_data)
        return {
            "fraud_probability": round(probability * 100, 2),
            "is_fraud": probability >= self.loader.threshold,
        }


model_path = BASE_DIR / "model" / "fraud_pipeline.joblib"
model_loader = ModelLoader(model_path)
prediction_service = PredictionService(model_loader)

#single prediction endpoint, accpets validated JSON and returns JSON response
@app.post("/predict")
def predict(tx: Transaction):
    transaction_data = tx.dict() #converts pydantic object to python dictionary expected by the prediction layer
    result = prediction_service.predict_fraud(transaction_data)

    return {
        "prediction": 1 if result["is_fraud"] else 0,
        "label": "fraud" if result["is_fraud"] else "not_fraud",
        "probability": result["fraud_probability"]
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
