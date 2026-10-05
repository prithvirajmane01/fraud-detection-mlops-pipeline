import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os


print("Generating dataset...")

np.random.seed(42)
n_samples=10000

data={
    "transaction_amount": np.random.exponential(scale=100, size=n_samples),
    "transaction_hour":   np.random.randint(0, 24, size=n_samples),
    "days_since_last_transaction": np.random.randint(0, 30, size=n_samples),
    "customer_age":       np.random.randint(18, 80, size=n_samples),
    "is_foreign_transaction": np.random.randint(0, 2, size=n_samples),
    "num_transactions_today": np.random.randint(1, 20, size=n_samples),
}

df=pd.DataFrame(data)

fraud_condition=(
    (df["transaction_amount"] > 300) &
    (df["is_foreign_transaction"] == 1) &
    (df["num_transactions_today"] > 10)
)

df["is_fraud"] = 0
df.loc[fraud_condition, "is_fraud"]=1

print(f"Total transactions : {len(df)}")
print(f"Fraudulent         : {df['is_fraud'].sum()}")
print(f"Legitimate         : {(df['is_fraud'] == 0).sum()}")


print("\nTraining model...")

X=df.drop("is_fraud", axis=1)
y=df["is_fraud"]

X_train, X_test, y_train, y_test=train_test_split(
    X, y, test_size=0.2, random_state=42
)

model=RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("\nModel Performance:")
y_pred=model.predict(X_test)
print(classification_report(y_test, y_pred))


# STEP 5: Save the model to a file
# ─────────────────────────────────────────────
os.makedirs("app/model", exist_ok=True)
joblib.dump(model, "app/model/fraud_model.pkl")
print("Model saved to app/model/fraud_model.pkl")
