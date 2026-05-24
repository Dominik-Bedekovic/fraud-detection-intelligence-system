import io
from pathlib import Path
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import joblib
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Transaction as TransactionModel
from backend.app.models import PredictionResult

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
import sys
sys.path.append(str(PROJECT_ROOT))
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "frontend"), name="static")

# pydantic validates incoming JSON and returns 422 on invalid input
class Transaction(BaseModel):
    type: str
    amount: float
    oldbalanceOrg: float
    newbalanceOrig: float
    oldbalanceDest: float
    newbalanceDest: float

# loads trained fraud model once during application startup
class ModelLoader:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.pipeline = None
        self.threshold = 0.1
        self.load_model()

    def load_model(self):
        try:
            bundle = joblib.load(self.model_path)
            # dict bundle with pipeline+threshold
            if isinstance(bundle, dict):  
                self.pipeline = bundle["pipeline"]
                self.threshold = bundle["threshold"]
            else:
                self.pipeline = bundle
        except Exception as e:
            print(f"error loading model: {e}")

    # predict fraud probability for one transaction
    def predict(self, data: dict) -> float:
        if self.pipeline is None:
            raise ValueError("model not loaded")
        df = pd.DataFrame([data])
        return float(self.pipeline.predict_proba(df)[0][1])

    # predict fraud probability for a batch of transactions (DataFrame)
    def predict_batch(self, df: pd.DataFrame):
        if self.pipeline is None:
            raise ValueError("model not loaded")
        return self.pipeline.predict_proba(df)[:, 1]

# converts probability into fraud/not fraud
class PredictionService:
    def __init__(self, loader: ModelLoader):
        self.loader = loader

    def predict_fraud(self, transaction_data: dict) -> dict:
        probability = self.loader.predict(transaction_data)
        return {
            "fraud_probability": round(float(probability) * 100, 2),
            "is_fraud": bool(probability >= self.loader.threshold),
        }

    def predict_fraud_batch(self, df: pd.DataFrame) -> list:
        probabilities = self.loader.predict_batch(df)
        results = []
        for prob in probabilities:
            results.append({
                "fraud_probability": round(float(prob) * 100, 2),
                "is_fraud": bool(prob >= self.loader.threshold)
            })
        return results

model_path = BASE_DIR / "model" / "fraud_pipeline.joblib"
model_loader = ModelLoader(model_path)
prediction_service = PredictionService(model_loader)

# single prediction endpoint, accepts validated JSON and returns JSON response
@app.get("/")
async def serve_frontend():
    return FileResponse(PROJECT_ROOT / "frontend" / "index.html")


@app.get("/db/health")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}



@app.post("/predict")
def predict(tx: Transaction, db: Session = Depends(get_db)):
    transaction_data = tx.dict() # converts pydantic object to python dictionary
    transaction_data["step"] = 1
    result = prediction_service.predict_fraud(transaction_data)

    #save input to database
    db_tx = TransactionModel (
        type = tx.type,
        amount = tx.amount,
        oldbalanceOrg = tx.oldbalanceOrg,
        newbalanceOrig = tx.newbalanceOrig,
        oldbalanceDest = tx.oldbalanceDest,
        newbalanceDest = tx.newbalanceDest,
        step = 1,
        source = "single"
    )

    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)

    #save prediction to database
    db_prediction = PredictionResult (
        transaction_id = db_tx.id,
        prediction = 1 if result["is_fraud"] else 0,
        label = "fraud" if result["is_fraud"] else "not_fraud",
        probability = result["fraud_probability"] / 100 
    )

    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)

    return {
        "prediction": db_prediction.prediction,
        "label": db_prediction.label,
        "probability": db_prediction.probability * 100
    }

# batch prediction endpoint, accepts CSV file and returns JSON list of predictions
@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {e}")
    
    results = prediction_service.predict_fraud_batch(df)
    
    formatted_results = [
        {
            "prediction": 1 if res["is_fraud"] else 0,
            "label": "fraud" if res["is_fraud"] else "not_fraud",
            "probability": res["fraud_probability"]
        }
        for res in results
    ]
    return {"results": formatted_results}

#Pass the transaction history values to the HTML page from the database
@app.get("/transactions")
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(TransactionModel).all()

    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "type": t.type,
            "amount": t.amount,
            "prediction": t.prediction_result.prediction if t.prediction_result else None,
            "probability": t.prediction_result.probability if t.prediction_result else None,
        })

    return result

if __name__ == "__main__":
    import uvicorn
    # Updated to python -m uvicorn based on the issue discussion
    uvicorn.run(app, host="127.0.0.1", port=8000)
