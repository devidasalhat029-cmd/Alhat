import pandas as pd
import random

data = []

for i in range(1000):

    temperature = round(random.uniform(15, 40), 2)
    humidity = round(random.uniform(30, 95), 2)
    soil_moisture = round(random.uniform(10, 90), 2)
    rainfall = round(random.uniform(0, 250), 2)

    # Simple irrigation rule for generating training labels
    if soil_moisture < 35 and rainfall < 50:
        irrigation_required = 1
    else:
        irrigation_required = 0

    data.append([
        temperature,
        humidity,
        soil_moisture,
        rainfall,
        irrigation_required
    ])


df = pd.DataFrame(
    data,
    columns=[
        "temperature",
        "humidity",
        "soil_moisture",
        "rainfall",
        "irrigation_required"
    ]
)

df.to_csv(
    "irrigation_dataset.csv",
    index=False
)

print("irrigation_dataset.csv created successfully!")
print("\nDataset shape:", df.shape)
print("\nClass distribution:")
print(df["irrigation_required"].value_counts())