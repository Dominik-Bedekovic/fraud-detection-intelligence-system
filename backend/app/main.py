from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import pandas as pd
import joblib


app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


class ModelLoader:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.pipeline = None
        self.load_model()

    def load_model(self):
        try:
            bundle = joblib.load(self.model_path)
            self.pipeline = bundle["pipeline"]
        except Exception as e:
            print(f"error loading model: {e}")

    def predict(self, data: dict) -> float:
        if not self.pipeline:
            raise ValueError("model not loaded")
        df = pd.DataFrame([data])
        return self.pipeline.predict_proba(df)[0][1]


class PredictionService:
    def __init__(self, loader: ModelLoader):
        self.loader = loader

    def predict_fraud(self, transaction_data: dict) -> dict:
        probability = self.loader.predict(transaction_data)
        return {
            "fraud_probability": round(probability * 100, 2),
            "is_fraud": probability >= 0.5,
        }


model_path = str(BASE_DIR / "model" / "fraud_pipeline.joblib")
model_loader = ModelLoader(model_path)
prediction_service = PredictionService(model_loader)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/")
async def predict(
    request: Request,
    step: int = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    oldBalanceOrig: float = Form(...),
    newBalanceOrig: float = Form(...),
    oldBalanceDest: float = Form(...),
    newBalanceDest: float = Form(...),
):
    transaction_data = {
        "step": step,
        "type": type,
        "amount": amount,
        "oldbalanceOrg": oldBalanceOrig,
        "newbalanceOrig": newBalanceOrig,
        "oldbalanceDest": oldBalanceDest,
        "newbalanceDest": newBalanceDest,
    }

    result = prediction_service.predict_fraud(transaction_data)
    return f"Fraud probability: {result['fraud_probability']}%"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
