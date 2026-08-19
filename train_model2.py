import os
import cv2
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report


DATASET_DIR = "dataset/color"
MODEL_DIR = "models"

IMAGE_SIZE = (128, 128)


def extract_features(image_path):
    image = cv2.imread(image_path)

    if image is None:
        return None

    image = cv2.resize(image, IMAGE_SIZE)

    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # HOG-like simple feature using resized grayscale image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Normalize
    gray = gray.astype(np.float32) / 255.0

    # Color features
    hsv = hsv.astype(np.float32) / 255.0

    features = np.concatenate([
        gray.flatten(),
        hsv.flatten()
    ])

    return features


def load_dataset():

    X = []
    y = []

    if not os.path.exists(DATASET_DIR):
        print("Dataset folder not found!")
        return X, y

    for class_name in os.listdir(DATASET_DIR):

        class_path = os.path.join(DATASET_DIR, class_name)

        if not os.path.isdir(class_path):
            continue

        print("Loading:", class_name)

        for filename in os.listdir(class_path):

            file_path = os.path.join(class_path, filename)

            if not filename.lower().endswith(
                (".jpg", ".jpeg", ".png", ".webp")
            ):
                continue

            features = extract_features(file_path)

            if features is not None:
                X.append(features)
                y.append(class_name)

    return np.array(X), np.array(y)


print("\nLoading dataset...\n")

X, y = load_dataset()

print("\nTotal images:", len(X))

if len(X) == 0:
    print("No images found.")
    exit()

# Encode class names
encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

# Save encoder
os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(
    encoder,
    os.path.join(MODEL_DIR, "label_encoder.pkl")
)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_encoded,
    test_size=0.20,
    random_state=42,
    stratify=y_encoded
)

print("Training images:", len(X_train))
print("Testing images:", len(X_test))

# SVM model
model = SVC(
    kernel="rbf",
    probability=False,
    C=10,
    gamma="scale"
)

print("\nTraining model...\n")

model.fit(X_train, y_train)

# Test
predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print("\n==============================")
print("MODEL TRAINING COMPLETED")
print("==============================")

print("Accuracy:", round(accuracy * 100, 2), "%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        predictions,
        target_names=encoder.classes_
    )
)

# Save model
model_path = os.path.join(
    MODEL_DIR,
    "disease_model.pkl"
)

joblib.dump(model, model_path)

print("\nModel saved:")
print(model_path)

print("\nLabel encoder saved:")
print(
    os.path.join(
        MODEL_DIR,
        "label_encoder.pkl"
    )
)