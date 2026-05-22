from fastapi import FastAPI

app = FastAPI()

products = {
    1: {"product_id": 1, "name": "Laptop", "price": 999.99},
    2: {"product_id": 2, "name": "Mouse", "price": 25.50},
    3: {"product_id": 3, "name": "Keyboard", "price": 75.00}
}

@app.get("/")
def root():
    return {"service": "product-service", "status": "running"}

@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = products.get(product_id)
    if product:
        return product
    return {"error": "Product not found"}
