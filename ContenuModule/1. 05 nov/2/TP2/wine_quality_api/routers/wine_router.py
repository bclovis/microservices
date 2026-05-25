from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
import pandas as pd
from pathlib import Path
from models import WineData, WineResponse, User
from dependencies import get_current_active_user

router = APIRouter()
DATA_PATH = Path(__file__).parent.parent / "data" / "WineQT.csv"

def load_wines_df() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise HTTPException(status_code=500, detail="Dataset not found")
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.replace(' ', '_')
    if 'Id' in df.columns:
        df = df.drop('Id', axis=1)
    return df

def save_wines_df(df: pd.DataFrame):
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.replace('_', ' ')
    df_copy.to_csv(DATA_PATH, index=False)

@router.get("/", response_model=List[WineResponse])
async def get_all_wines(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    df = load_wines_df()
    wines_subset = df.iloc[skip:skip + limit]
    wines = []
    for idx, row in wines_subset.iterrows():
        wine_dict = row.to_dict()
        wine_dict['id'] = int(idx)
        wines.append(wine_dict)
    return wines

@router.get("/{wine_id}", response_model=WineResponse)
async def get_wine(wine_id: int):
    df = load_wines_df()
    if wine_id < 0 or wine_id >= len(df):
        raise HTTPException(status_code=404, detail="Wine not found")
    wine_dict = df.iloc[wine_id].to_dict()
    wine_dict['id'] = wine_id
    return wine_dict

@router.post("/", response_model=WineResponse, status_code=201)
async def create_wine(wine: WineData, current_user: User = Depends(get_current_active_user)):
    df = load_wines_df()
    wine_dict = wine.model_dump()
    new_wine_df = pd.DataFrame([wine_dict])
    df = pd.concat([df, new_wine_df], ignore_index=True)
    save_wines_df(df)
    wine_id = len(df) - 1
    wine_dict['id'] = wine_id
    return wine_dict

@router.put("/{wine_id}", response_model=WineResponse)
async def update_wine(wine_id: int, wine: WineData, current_user: User = Depends(get_current_active_user)):
    df = load_wines_df()
    if wine_id < 0 or wine_id >= len(df):
        raise HTTPException(status_code=404, detail="Wine not found")
    wine_dict = wine.model_dump()
    for key, value in wine_dict.items():
        df.at[wine_id, key] = value
    save_wines_df(df)
    wine_dict['id'] = wine_id
    return wine_dict

@router.delete("/{wine_id}", status_code=204)
async def delete_wine(wine_id: int, current_user: User = Depends(get_current_active_user)):
    df = load_wines_df()
    if wine_id < 0 or wine_id >= len(df):
        raise HTTPException(status_code=404, detail="Wine not found")
    df = df.drop(wine_id)
    df = df.reset_index(drop=True)
    save_wines_df(df)
    return None
