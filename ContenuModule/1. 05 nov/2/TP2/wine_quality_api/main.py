from fastapi import FastAPI
import uvicorn
from routers.auth_router import router as auth_router
from routers.wine_router import router as wine_router

app = FastAPI(title="Wine Quality API")

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(wine_router, prefix="/wines", tags=["wines"])

@app.get("/")
async def root():
    return {"message": "Wine Quality API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
