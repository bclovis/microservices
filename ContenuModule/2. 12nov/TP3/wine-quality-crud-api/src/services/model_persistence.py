from joblib import load, dump
import os

class ModelPersistence:
    def __init__(self, model_path='models_storage/wine_model.joblib'):
        self.model_path = model_path

    def save_model(self, model):
        """Save the trained model to disk."""
        try:
            dump(model, self.model_path)
            return {"success": True, "message": "Model saved successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def load_model(self):
        """Load the trained model from disk."""
        if not os.path.exists(self.model_path):
            return {"success": False, "error": "Model file not found."}
        
        try:
            model = load(self.model_path)
            return {"success": True, "model": model}
        except Exception as e:
            return {"success": False, "error": str(e)}