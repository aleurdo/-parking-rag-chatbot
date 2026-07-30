from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.admin_routes import admin_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.models import Base
    from app.db.session import get_engine
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="ParkEase RAG Chatbot",
        description="Parking reservation chatbot with RAG, admin approval, and MCP recording",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(admin_router)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
