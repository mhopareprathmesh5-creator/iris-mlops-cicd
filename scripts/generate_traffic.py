"""Send realistic traffic to the deployed app so Prometheus and Grafana have data.

Usage: python scripts/generate_traffic.py [requests] [base_url]
"""
import json
import random
import sys
import time
import urllib.error
import urllib.request

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5000"
# typical measurements (mean, std) per species: sepal_length, sepal_width, petal_length, petal_width
PROFILES = {
    "setosa": [(5.0, .35), (3.4, .38), (1.46, .17), (.25, .1)],
    "versicolor": [(5.9, .52), (2.8, .31), (4.26, .47), (1.33, .2)],
    "virginica": [(6.6, .64), (3.0, .32), (5.55, .55), (2.03, .27)],
}
NAMES = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
random.seed(7)
counts, invalid, errors = {}, 0, 0

for i in range(N):
    if random.random() < 0.08:                       # some bad requests, as real users make
        body = {"sepal_length": "abc", "sepal_width": 3.0}
    else:
        prof = PROFILES[random.choice(list(PROFILES))]
        body = {n: round(max(0.1, random.gauss(m, s)), 2) for n, (m, s) in zip(NAMES, prof)}
    req = urllib.request.Request(f"{BASE}/api/predict", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        species = json.load(urllib.request.urlopen(req, timeout=5))["species"]
        counts[species] = counts.get(species, 0) + 1
    except urllib.error.HTTPError as e:
        invalid += e.code == 400
        errors += e.code != 400
    if i % 3 == 0:
        urllib.request.urlopen(f"{BASE}/", timeout=5).read()
    time.sleep(0.15)

print(f"sent {N} prediction requests to {BASE}")
print(f"predicted: {dict(sorted(counts.items()))}")
print(f"rejected as invalid (HTTP 400): {invalid}   other errors: {errors}")
