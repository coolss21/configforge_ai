import logging
import traceback
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Literal
from app.compiler.pipeline import CompilerPipeline

logger = logging.getLogger("configforge.api")

router = APIRouter()

class GenerateRequest(BaseModel):
    prompt: str
    mode: Literal["fast", "quality"] = "quality"

@router.post("/generate")
async def generate(request: GenerateRequest):
    try:
        pipeline = CompilerPipeline()
        result = await pipeline.generate(request.prompt, request.mode)
        return result
    except Exception as exc:
        logger.error(f"Pipeline error: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "detail": "Pipeline execution failed"}
        )
