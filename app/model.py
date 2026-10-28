"""Train and load the Iris classifier used by the web application."""
import os

import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

FEATURES = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
SPECIES = ["setosa", "versicolor", "virginica"]
MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(os.path.dirname(__file__), "model.joblib"))


def train(path: str = MODEL_PATH) -> float:
    """Train a Random Forest, save it with its test accuracy, return the accuracy."""
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42).fit(X_train, y_train)
    accuracy = accuracy_score(y_test, model.predict(X_test))
    joblib.dump({"model": model, "accuracy": accuracy}, path)
    return accuracy


def load(path: str = MODEL_PATH):
    if not os.path.exists(path):
        train(path)
    bundle = joblib.load(path)
    return bundle["model"], bundle["accuracy"]


if __name__ == "__main__":
    print(f"Model trained - test accuracy {train():.3f} - saved to {MODEL_PATH}")
