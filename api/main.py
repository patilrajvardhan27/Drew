import asyncio
import contextlib
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.auth.reset import router as reset_router
from api.auth.routes import router as auth_router
from api.blocks.routes import router as blocks_router
from api.core.cleanup import purge_forever
from api.core.config import get_settings
from api.core.db import init_db
from api.core.errors import install_handlers
from api.documents.routes import router as documents_router
from api.export.cors import express_cors
from api.export.routes import router as export_router
from api.pages.routes import router as pages_router


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    purge = asyncio.create_task(purge_forever(get_settings()))
    yield
    purge.cancel()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Redraft API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    install_handlers(app)

    # Added last so it wraps the general CORS policy for the one route add-ons call.
    app.middleware("http")(express_cors)

    for router in (auth_router, reset_router, documents_router, blocks_router, pages_router, export_router):
        app.include_router(router, prefix="/api")

    @app.get("/api/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ok"}

    dist = settings.web_dist.resolve()
    if dist.is_dir():
        # One container can serve the built web app too; unknown paths fall back to the SPA.
        @app.get("/{path:path}", include_in_schema=False)
        def web(path: str) -> FileResponse:
            target = (dist / path).resolve()
            if path and target.is_file() and target.is_relative_to(dist):
                return FileResponse(target)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
