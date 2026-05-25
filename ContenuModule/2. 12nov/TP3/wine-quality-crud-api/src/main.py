from fastapi import FastAPI
from routers.auth_router import router as auth_router
from routers.wine_router import router as wine_router

app = FastAPI(
    title="Wine Quality CRUD API",
    description="API for managing wine dataset with authentication",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(wine_router, prefix="/wines", tags=["Wines"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Wine Quality CRUD API. Use /docs for documentation."}