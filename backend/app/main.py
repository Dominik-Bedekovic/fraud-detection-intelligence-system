import io
from pathlib import Path
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException
from fastapi import status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import joblib
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.auth import router,get_current_user,require_admin,require_analyst_or_admin
from backend.app.models import User
from backend.app import models as db_models
from typing import Annotated

app = FastAPI()

#mount /auth endpoints
app.include_router(router)

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
import sys
sys.path.append(str(PROJECT_ROOT))
app.mount("/static", StaticFiles(directory=PROJECT_ROOT / "frontend"), name="static")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

#request schema
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
        self.model_name = None
        self.model_version = None
        self.load_model()

    def load_model(self):
        try:
            bundle = joblib.load(self.model_path)
            # dict bundle with pipeline+threshold
            if isinstance(bundle, dict):  
                self.pipeline = bundle.get("pipeline")
                self.threshold = bundle.get("threshold",0.1)
                self.model_name = bundle.get("model_name")
                self.model_version = bundle.get("features_version")
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

#frontend route
@app.get("/")
async def serve_frontend():
    return FileResponse(PROJECT_ROOT / "frontend" / "index.html")

#auth test endpoint
@app.get("/users", status_code=status.HTTP_200_OK)
async def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail= 'Authentication failed')
    return{"user": user}


#who am i endpoint, returns object from DB,also lists user transactions
@app.get("/auth/me")
def me(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(
        User.id == user["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "id": db_user.id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "role_id": db_user.role_id,
        "transactions": [
            {
                "id": tx.id,
                "type": tx.type,
                "amount": tx.amount,
                "created_at": tx.created_at
            }
            for tx in db_user.transactions
        ]
    }

#lists all users, only for admins
@app.get("/admin/users")
def get_all_users(
    user=Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role_id": u.role_id,
            "is_active": u.is_active,
            "is_email_verified": u.is_email_verified,
            "created_at": u.created_at
        }
        for u in users
    ]

#db health check
@app.get("/db/health")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}

#roles debug endpoint, should remove before merge
@app.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    roles = db.execute(
        text("SELECT * FROM roles")
    ).fetchall()

    return [dict(row._mapping) for row in roles] #remove before merge



#single predicition endpoint
@app.post("/predict")
def predict(
    tx: Transaction,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
    ):
    transaction_data = tx.model_dump() # converts pydantic object to python dictionary
    transaction_data["step"] = 1
    result = prediction_service.predict_fraud(transaction_data)

    # save transaction linked to atuhenticated user to db
    db_tx = db_models.Transaction(
        user_id=user["user_id"],
        type=tx.type,
        amount=tx.amount,
        oldbalanceOrg=tx.oldbalanceOrg,
        newbalanceOrig=tx.newbalanceOrig,
        oldbalanceDest=tx.oldbalanceDest,
        newbalanceDest=tx.newbalanceDest,
        step=1,
        source="single"
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)

    # save the prediction result too
    db_pred = db_models.PredictionResult(
        transaction_id=db_tx.id,
        prediction=1 if result["is_fraud"] else 0,
        label="fraud" if result["is_fraud"] else "not_fraud",
        probability=result["fraud_probability"],
        model_name=model_loader.model_name,
        model_version=model_loader.model_version,
        threshold=model_loader.threshold
    )
    db.add(db_pred)
    db.commit()

    return {
        "prediction": 1 if result["is_fraud"] else 0,
        "label": "fraud" if result["is_fraud"] else "not_fraud",
        "probability": result["fraud_probability"]
    }

# batch prediction endpoint, accepts CSV file and returns JSON list of predictions
@app.post("/predict/batch")
async def predict_batch(
    file: UploadFile = File(...),
    db: Session= Depends(get_db),
    user=Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {e}")
    
    results = prediction_service.predict_fraud_batch(df)
    
    db_transactions = []
    for index, row in df.iterrows():
        db_tx = db_models.Transaction(
            user_id=user["user_id"],
            type=str(row.get("type", "UNKNOWN")),
            amount=float(row.get("amount", 0.0)),
            oldbalanceOrg=float(row.get("oldbalanceOrg", 0.0)),
            newbalanceOrig=float(row.get("newbalanceOrig", 0.0)),
            oldbalanceDest=float(row.get("oldbalanceDest", 0.0)),
            newbalanceDest=float(row.get("newbalanceDest", 0.0)),
            step=int(row.get("step", 1)),
            source="batch"
        )
        db.add(db_tx)
        db_transactions.append(db_tx)

    db.commit()

    formatted_results = []
    # loop through the predictions and link them to the transactions we just saved
    for i, res in enumerate(results):
        db_pred = db_models.PredictionResult(
            transaction_id=db_transactions[i].id,
            prediction=1 if res["is_fraud"] else 0,
            label="fraud" if res["is_fraud"] else "not_fraud",
            probability=res["fraud_probability"],
            model_name=model_loader.model_name,
            model_version=model_loader.model_version,
            threshold=model_loader.threshold
        )
        db.add(db_pred)

        formatted_results.append({
            "prediction": 1 if res["is_fraud"] else 0,
            "label": "fraud" if res["is_fraud"] else "not_fraud",
            "probability": res["fraud_probability"]
        })

    db.commit()

    return {"results": formatted_results}

if __name__ == "__main__":
    import uvicorn
    # Updated to python -m uvicorn based on the issue discussion
    uvicorn.run(app, host="127.0.0.1", port=8000)
