from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cryptography.fernet import Fernet
import base64
import os

# dino encrypted secret
app = FastAPI(title="Pokemon Drafter - Encryption Service")

# Generate or load encryption key
encryption_key = os.getenv("ENCRYPTION_KEY", "pokemon_encryption_key_123456789")
# Convert to valid Fernet key (must be 32 url-safe base64-encoded bytes)
fernet_key = base64.urlsafe_b64encode(encryption_key.encode().ljust(32)[:32])
cipher_suite = Fernet(fernet_key)

class EncryptRequest(BaseModel):
    data: str

class DecryptRequest(BaseModel):
    encrypted_data: str

@app.post("/encrypt")
async def encrypt_data(request: EncryptRequest):
    """Encrypt data for inter-backend communication"""
    try:
        encrypted = cipher_suite.encrypt(request.data.encode())
        return {
            "encrypted_data": base64.b64encode(encrypted).decode(),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decrypt")
async def decrypt_data(request: DecryptRequest):
    """Decrypt data from other backend"""
    try:
        encrypted = base64.b64decode(request.encrypted_data)
        decrypted = cipher_suite.decrypt(encrypted)
        return {
            "data": decrypted.decode(),
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
