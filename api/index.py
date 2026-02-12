from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .lotto_core import LottoFetcher, PatternAnalyzer, LottoGenerator
import os

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engine
# Note: In serverless, global state might reset, but that's okay for this Logic
fetcher = LottoFetcher()
# Attempt quick update (timeout protected in core)
fetcher.update_history(200)

analyzer = PatternAnalyzer(fetcher.get_last_n_rounds(200))
analyzer.calibrate()
generator = LottoGenerator(analyzer)

@app.get("/api")
def read_root():
    return {"status": "LottoLogic API Ready"}

@app.get("/api/generate")
def generate_numbers():
    results = []
    for _ in range(5):
        nums, score, details = generator.generate()
        results.append({
            "numbers": nums,
            "resonance_score": round(score, 1),
            "details": details
        })
    results.sort(key=lambda x: x['resonance_score'], reverse=True)
    return {"status": "success", "data": results}

@app.get("/api/stats")
def get_stats():
    return {
        "status": "success", 
        "data": {
            "weights": analyzer.weights,
            "history_count": len(analyzer.history)
        }
    }
