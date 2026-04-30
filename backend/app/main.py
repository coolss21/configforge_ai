from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import routes_health, routes_generate, routes_evaluate

logger = logging.getLogger("configforge")

app = FastAPI(title="ConfigForge AI", description="Compiler-Style AI App Configuration Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router)
app.include_router(routes_generate.router)
app.include_router(routes_evaluate.router)

@app.get("/")
def read_root():
    return {
        "status": "ConfigForge AI Backend is Running",
        "docs_url": "/docs",
        "frontend_note": "This is the API backend. Please visit the Vercel URL for the UI."
    }
