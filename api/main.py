from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import os

app = FastAPI()

# Enable CORS for all origins and all methods (handles OPTIONS preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow any origin
    allow_credentials=True,
    allow_methods=["*"],        # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],        # allow any headers
)

# Load telemetry JSON from the same folder (Vercel deployment safe)
json_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(json_path, "r") as f:
    telemetry = json.load(f)

# GET route for testing deployment
@app.get("/")
async def root():
    return {"message": "FastAPI telemetry API is live!"}

# POST route for telemetry metrics
@app.post("/metrics")
async def get_metrics(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"error": "Invalid JSON"}

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}
    for region in regions:
        # Filter records for this region
        records = [r for r in telemetry if r["region"] == region]
        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(sum(1 for l in latencies if l > threshold))

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
