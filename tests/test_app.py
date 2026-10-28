"""Unit tests run in the Docker 'test' stage - a failing test stops the CI/CD pipeline."""
import pytest

from app.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


SETOSA = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
VIRGINICA = {"sepal_length": 6.9, "sepal_width": 3.1, "petal_length": 5.4, "petal_width": 2.1}


def test_health(client):
    r = client.get("/health")
    body = r.get_json()
    assert r.status_code == 200 and body["status"] == "ok"
    assert body["model"] == "RandomForestClassifier"


def test_home_page_has_form(client):
    r = client.get("/")
    assert r.status_code == 200 and b"Iris Species Predictor" in r.data and b"<form" in r.data


@pytest.mark.parametrize("sample, species", [(SETOSA, "setosa"), (VIRGINICA, "virginica")])
def test_api_predicts_known_flowers(client, sample, species):
    body = client.post("/api/predict", json=sample).get_json()
    assert body["species"] == species
    assert abs(sum(body["probabilities"].values()) - 1) < 0.01


def test_form_prediction(client):
    r = client.post("/predict", data=SETOSA)
    assert r.status_code == 200 and b"Predicted species: setosa" in r.data


@pytest.mark.parametrize("bad", [
    {"sepal_length": 5.1},                                   # missing fields
    {**SETOSA, "petal_width": "abc"},                        # not a number
    {**SETOSA, "sepal_length": -3},                          # out of range
])
def test_invalid_input_is_rejected(client, bad):
    r = client.post("/api/predict", json=bad)
    assert r.status_code == 400 and "error" in r.get_json()


def test_model_accuracy_quality_gate(client):
    assert client.get("/health").get_json()["model_accuracy"] >= 0.90


def test_metrics_endpoint(client):
    client.post("/api/predict", json=SETOSA)
    text = client.get("/metrics").data.decode()
    assert "iris_predictions_total" in text and "iris_model_accuracy" in text
