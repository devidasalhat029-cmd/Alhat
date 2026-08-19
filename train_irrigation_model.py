import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# Load dataset
df = pd.read_csv("irrigation_dataset.csv")

print("Dataset loaded successfully!")
print(df.head())

print("\nDataset shape:")
print(df.shape)

print("\nColumns:")
print(df.columns)


# Features
X = df[
    [
        "temperature",
        "humidity",
        "soil_moisture",
        "rainfall"
    ]
]


# Target
y = df["irrigation_required"]


# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# Random Forest
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)


# Train
print("\nTraining model...")

model.fit(
    X_train,
    y_train
)


# Test
y_pred = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n==============================")
print("SMART IRRIGATION MODEL")
print("==============================")

print(
    "Accuracy:",
    round(accuracy * 100, 2),
    "%"
)

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# Save model
joblib.dump(
    model,
    "irrigation_model.pkl"
)

print("\n==============================")
print("irrigation_model.pkl created successfully!")
print("==============================")