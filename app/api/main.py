from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
import joblib
import numpy as np
import os
import sys

ROOT_DIR=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from app.db.database import Prediction, get_db
from app.api.auth import authenticate_user, create_access_token, get_current_user

# Create the FastAPI app
app=FastAPI(
    title="Fraud Detection API",
    description="Real-time fraud detection using a Random Forest model",
    version="1"
)

# Load the trained model
BASE_DIR=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model=joblib.load(os.path.join(BASE_DIR, "model", "fraud_model.pkl"))

# Define what a transaction looks like
class Transaction(BaseModel):
    transaction_amount: float
    transaction_hour: int
    days_since_last_transaction: int
    customer_age: int
    is_foreign_transaction: int
    num_transactions_today: int

@app.get("/")
def health_check():
    return {"status": "Fraud Detection API is running"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user=authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/predict")
def predict(
    transaction:Transaction,
    db: Session=Depends(get_db),
    current_user: str= Depends(get_current_user)
):
    features = np.array([[
        transaction.transaction_amount,
        transaction.transaction_hour,
        transaction.days_since_last_transaction,
        transaction.customer_age,
        transaction.is_foreign_transaction,
        transaction.num_transactions_today
    ]])

    prediction=model.predict(features)[0]
    probability=model.predict_proba(features)[0][1]
    verdict="FRAUD" if prediction==1 else "LEGITIMATE"

    try:
        record=Prediction(
            transaction_amount=transaction.transaction_amount,
            transaction_hour=transaction.transaction_hour,
            days_since_last_transaction=transaction.days_since_last_transaction,
            customer_age=transaction.customer_age,
            is_foreign_transaction=transaction.is_foreign_transaction,
            num_transactions_today=transaction.num_transactions_today,
            prediction=int(prediction),
            fraud_probability=round(float(probability), 4),
            verdict=verdict
        )
        db.add(record)
        db.commit()
        print("SUCCESS: Prediction saved to database")
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        db.rollback()

    return {
        "prediction": int(prediction),
        "fraud_probability": round(float(probability), 4),
        "verdict": verdict,
        "processed_by": current_user
    }

@app.get("/history")
def get_history(
    db: Session=Depends(get_db),
    current_user: str=Depends(get_current_user)
):
    records=db.query(Prediction).order_by(Prediction.id.desc()).limit(10).all()
    return records
