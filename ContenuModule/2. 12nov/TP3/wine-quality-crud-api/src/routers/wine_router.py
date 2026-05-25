from fastapi import APIRouter, HTTPException
from typing import List
from models.wine_models import Wine, WineCreate, WineUpdate
from services.wine_service import WineService

router = APIRouter()
wine_service = WineService()

@router.post("/wines/", response_model=Wine)
async def create_wine(wine: WineCreate):
    try:
        return await wine_service.create_wine(wine)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wines/", response_model=List[Wine])
async def read_wines(skip: int = 0, limit: int = 10):
    try:
        return await wine_service.get_wines(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/wines/{wine_id}", response_model=Wine)
async def read_wine(wine_id: int):
    try:
        wine = await wine_service.get_wine(wine_id)
        if wine is None:
            raise HTTPException(status_code=404, detail="Wine not found")
        return wine
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/wines/{wine_id}", response_model=Wine)
async def update_wine(wine_id: int, wine: WineUpdate):
    try:
        updated_wine = await wine_service.update_wine(wine_id, wine)
        if updated_wine is None:
            raise HTTPException(status_code=404, detail="Wine not found")
        return updated_wine
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/wines/{wine_id}", response_model=Wine)
async def delete_wine(wine_id: int):
    try:
        deleted_wine = await wine_service.delete_wine(wine_id)
        if deleted_wine is None:
            raise HTTPException(status_code=404, detail="Wine not found")
        return deleted_wine
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))