from fastapi import APIRouter
from api.v1.parser_agent import router as llm_router
v1_router = APIRouter(prefix="/v1")

v1_router.include_router(llm_router, prefix="/llm")