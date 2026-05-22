import asyncio
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from sqlalchemy import select

USERS = [
    {
        "username": "red_trainer",
        "email": "red@pokedrafter.com",
        "password": "RedTeam123!",
        "first_name": "Ash",
        "last_name": "Ketchum",
        "color": "RED",
        "level": 10,
        "points": 500,
    },
    {
        "username": "blue_trainer",
        "email": "blue@pokedrafter.com",
        "password": "BlueTeam123!",
        "first_name": "Gary",
        "last_name": "Oak",
        "color": "BLUE",
        "level": 10,
        "points": 480,
    },
    {
        "username": "admin",
        "email": "admin@pokedrafter.com",
        "password": "Admin123!",
        "first_name": "Professor",
        "last_name": "Oak",
        "color": None,
        "level": 99,
        "points": 9999,
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        for data in USERS:
            result = await db.execute(
                select(User).where(User.email == data["email"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f" User {data['email']} already exists, skipping...")
                continue

            user = User(
                username=data["username"],
                email=data["email"],
                password_hash=hash_password(data["password"]),
                first_name=data["first_name"],
                last_name=data["last_name"],
                color=data["color"],
                level=data["level"],
                points=data["points"],
            )
            db.add(user)
            print(f"Created user: {data['username']} ({data['color']})")

        await db.commit()
        print("\n Seed completed!")


if __name__ == "__main__":
    asyncio.run(seed())