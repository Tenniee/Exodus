from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.database import init_db
from app.routes.auth import router as auth_router
from app.routes.newsletter import router as newsletter_router
from app.routes.artist import router as artist_router
from app.routes.song import router as song_router
from app.routes.video import router as video_router
from app.routes.artist_request import router as artist_request_router

app = FastAPI(
    title="Exodus record Label API",
    description="Exodus Record Label User Authentication and Management API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://192.168.1.6"] for more control
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
def on_startup():
    """
    This function runs once when the application starts
    It initializes the database and creates tables if they don't exist
    """
    print("🚀 Starting up the application...")
    print("📊 Initializing database...")
    init_db()  # Create all tables
    print("✅ Database initialized successfully!")

# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Include the authentication routes from routes/auth.py
# All routes from auth_router will now be available in the app
# They'll be accessible at /auth/signup, /auth/login, /auth/me
app.include_router(auth_router)
app.include_router(newsletter_router)
app.include_router(artist_router)
app.include_router(song_router)
app.include_router(video_router)
app.include_router(artist_request_router)



# You can add more routers here as your app grows:
# app.include_router(posts_router)
# app.include_router(comments_router)
# etc.

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
def root():
    """
    Root endpoint - simple welcome message
    This is the first thing users see when they visit the API
    """
    return {
        "message": "Welcome to the User Authentication API",
        "docs": "/docs",
        "endpoints": {
            "signup": "/auth/signup",
            "login": "/auth/login",
            "current_user": "/auth/me"
        }
    }
