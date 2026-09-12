from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.scan import router as scan_router
from app.routes.report import router as report_router
from app.routes.consumer import router as consumer_router


app = FastAPI(
    title="Legal Metrology Compliance Backend",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(scan_router)
app.include_router(report_router)
app.include_router(consumer_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "legal-metrology-backend",
    }


