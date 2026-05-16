from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import Base, engine
from app.routes import auth, complaints, categories, dashboard, feedback, notifications, attachments
from contextlib import asynccontextmanager
import asyncio, os

# Import all models so SQLAlchemy creates tables
from app.models import user, complaint, category, feedback as feedback_model, attachment, notification  # noqa

# Create all tables
Base.metadata.create_all(bind=engine)

async def escalation_scheduler():
    from app.utils.escalation import run_escalation_check
    while True:
        await asyncio.sleep(3600)  # run every hour
        try:
            run_escalation_check()
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(escalation_scheduler())
    yield

app = FastAPI(
    lifespan=lifespan,
    title="Customer Complaint & Resolution Tracking System",
    description="API for managing customer complaints",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(categories.router)
app.include_router(dashboard.router)
app.include_router(feedback.router)
app.include_router(notifications.router)
app.include_router(attachments.router)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
uploads_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/app/{page}")
def serve_page(page: str):
    return FileResponse(os.path.join(frontend_path, f"{page}.html"))
