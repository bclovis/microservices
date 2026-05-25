from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String, unique=True)
    quantity = Column(Integer)

Base.metadata.create_all(bind=engine)

def init_products():
    db = SessionLocal()
    if db.query(Product).count() == 0:
        products = [
            Product(product_id="prod-1", quantity=100),
            Product(product_id="prod-2", quantity=50),
            Product(product_id="prod-3", quantity=75),
        ]
        db.add_all(products)
        db.commit()
    db.close()

init_products()
