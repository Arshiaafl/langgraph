from fastapi import FastAPI
from routers import chat, upload

# Initialize FastAPI app
app = FastAPI(
    title="FastAPI OpenAI App",
    description="API with chat and upload endpoints using OpenAI GPT-4o",
    version="1.0.0"
)

# Include routers for chat and upload endpoints without /api prefix
app.include_router(chat.router, tags=["chat"])
app.include_router(upload.router, tags=["upload"])

# Root endpoint for basic health check
@app.get("/")
async def root():
    return {"message": "FastAPI OpenAI App is running"}