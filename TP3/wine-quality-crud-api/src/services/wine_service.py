from typing import List, Dict, Any
from fastapi import HTTPException
import pandas as pd
from models.wine_models import WineModel

class WineService:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.wine_data = self.load_data()

    def load_data(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.data_file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading data: {e}")

    def get_all_wines(self) -> List[Dict[str, Any]]:
        return self.wine_data.to_dict(orient="records")

    def get_wine(self, wine_id: int) -> Dict[str, Any]:
        wine = self.wine_data[self.wine_data['id'] == wine_id]
        if wine.empty:
            raise HTTPException(status_code=404, detail="Wine not found")
        return wine.to_dict(orient="records")[0]

    def create_wine(self, wine: WineModel) -> Dict[str, Any]:
        new_wine = wine.dict()
        new_wine['id'] = self.wine_data['id'].max() + 1
        self.wine_data = self.wine_data.append(new_wine, ignore_index=True)
        self.save_data()
        return new_wine

    def update_wine(self, wine_id: int, wine: WineModel) -> Dict[str, Any]:
        index = self.wine_data[self.wine_data['id'] == wine_id].index
        if index.empty:
            raise HTTPException(status_code=404, detail="Wine not found")
        self.wine_data.loc[index] = wine.dict()
        self.save_data()
        return self.wine_data.loc[index].to_dict()

    def delete_wine(self, wine_id: int) -> Dict[str, Any]:
        index = self.wine_data[self.wine_data['id'] == wine_id].index
        if index.empty:
            raise HTTPException(status_code=404, detail="Wine not found")
        self.wine_data = self.wine_data.drop(index)
        self.save_data()
        return {"detail": "Wine deleted successfully"}

    def save_data(self):
        try:
            self.wine_data.to_csv(self.data_file, index=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving data: {e}")