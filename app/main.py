import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import init_db
from app.routers import web, api_v1, billing

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure SQLite DB tables exist
    await init_db()
    yield
    # Shutdown

app = FastAPI(
    title="OmniExtract API",
    description="High-performance Web-to-Clean-Markdown API designed specifically for LLMs, RAG, and AI Agents.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware (Enable web apps & tools to call the API directly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(web.router)
app.include_router(api_v1.router)
app.include_router(billing.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
