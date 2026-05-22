from fastapi import FastAPI, HTTPException
import httpx

app = FastAPI()

@app.get("/")
def root():
    return {"service": "order-service", "status": "running"}

@app.post("/orders")
async def create_order(user_id: int, product_id: int):
    async with httpx.AsyncClient() as client:
        try:
            user_response = await client.get(f"http://user-service:8000/users/{user_id}")
            if user_response.status_code != 200:
                raise HTTPException(status_code=404, detail="User not found")
            user = user_response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling user-service: {str(e)}")
        
        try:
            product_response = await client.get(f"http://product-service:8000/products/{product_id}")
            if product_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Product not found")
            product = product_response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error calling product-service: {str(e)}")
    
    order = {
        "user": user["name"],
        "product": product["name"],
        "price": product["price"],
        "message": "Order Created"
    }
    
    return order
