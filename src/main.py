import uvicorn
from fastapi import FastAPI

from api.router import v1_router
from core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=settings.SWAGGER_URL,
    openapi_url=settings.openapi_url,
)
# Routers
app.include_router(v1_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        access_log=False,
        reload=True,
        reload_includes=[".env"]
    )
