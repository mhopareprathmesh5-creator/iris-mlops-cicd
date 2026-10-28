"""Iris Species Predictor - Flask ML web application with Prometheus metrics."""
import os
import time

from flask import Flask, Response, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, Info, generate_latest

from app.model import FEATURES, SPECIES, load

APP_VERSION = os.environ.get("APP_VERSION", "dev")

app = Flask(__name__)
model, model_accuracy = load()

# ---------------------------------------------------------------- Prometheus metrics
REQUESTS = Counter("iris_http_requests_total", "HTTP requests", ["endpoint", "method", "status"])
LATENCY = Histogram("iris_request_latency_seconds", "Request latency in seconds", ["endpoint"])
PREDICTIONS = Counter("iris_predictions_total", "Predictions made, by predicted species", ["species"])
INVALID = Counter("iris_invalid_requests_total", "Prediction requests rejected by validation")
ACCURACY = Gauge("iris_model_accuracy", "Test accuracy of the deployed model")
BUILD = Info("iris_app", "Application build information")
ACCURACY.set(model_accuracy)
BUILD.info({"version": APP_VERSION, "model": type(model).__name__})


@app.before_request
def _start_timer():
    request._start = time.perf_counter()


@app.after_request
def _record(response):
    if request.endpoint != "metrics":
        LATENCY.labels(request.path).observe(time.perf_counter() - request._start)
        REQUESTS.labels(request.path, request.method, str(response.status_code)).inc()
    return response


# ---------------------------------------------------------------- helpers
def parse_features(data):
    """Return the 4 features as floats, or raise ValueError with a readable message."""
    try:
        values = [float(data[name]) for name in FEATURES]
    except KeyError as missing:
        raise ValueError(f"missing field {missing}")
    except (TypeError, ValueError):
        raise ValueError("all measurements must be numbers")
    if not all(0 < v < 15 for v in values):
        raise ValueError("measurements must be between 0 and 15 cm")
    return values


def predict(values):
    proba = model.predict_proba([values])[0]
    idx = int(proba.argmax())
    PREDICTIONS.labels(SPECIES[idx]).inc()
    return {"species": SPECIES[idx], "confidence": round(float(proba[idx]), 3),
            "probabilities": {s: round(float(p), 3) for s, p in zip(SPECIES, proba)}}


# ---------------------------------------------------------------- routes
@app.route("/")
def home():
    return render_template("index.html", version=APP_VERSION, accuracy=model_accuracy)


@app.route("/predict", methods=["POST"])
def predict_form():
    try:
        result = predict(parse_features(request.form))
        return render_template("index.html", result=result, form=request.form,
                               version=APP_VERSION, accuracy=model_accuracy)
    except ValueError as err:
        INVALID.inc()
        return render_template("index.html", error=str(err), form=request.form,
                               version=APP_VERSION, accuracy=model_accuracy), 400


@app.route("/api/predict", methods=["POST"])
def predict_api():
    try:
        return jsonify(predict(parse_features(request.get_json(force=True, silent=True) or {})))
    except ValueError as err:
        INVALID.inc()
        return jsonify({"error": str(err)}), 400


@app.route("/health")
def health():
    return jsonify({"status": "ok", "version": APP_VERSION, "model": "RandomForestClassifier",
                    "model_accuracy": round(model_accuracy, 3)})


@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
