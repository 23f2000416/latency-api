from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json

app = FastAPI()

# Enable CORS for all origins and all methods (including OPTIONS preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow requests from any domain
    allow_credentials=True,
    allow_methods=["*"],        # Allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],        # Allow all headers
)

# Load telemetry JSON once (make sure path is correct for Vercel)
with open("./api/q-vercel-latency.json", "r") as f:
    telemetry = json.load(f)

@app.get("/")
def root():
    return {"message": "FastAPI telemetry API is live!"}

@app.post("/metrics")
async def get_metrics(request: Request):
    body = await request.json()
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
