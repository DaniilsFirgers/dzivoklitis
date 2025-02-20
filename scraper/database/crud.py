from sqlalchemy import func
from sqlalchemy.future import select
from scraper.database.models import Flat, Price, Favourite
from sqlalchemy.dialects.postgresql import insert
from scraper.database.postgres import postgres_instance


async def upsert_flat(flat: Flat, price: int) -> None:
    """Insert or update a flat and add its price."""
    async with postgres_instance.SessionLocal() as db:
        async with db.begin():  # Auto rollback on failure
            await db.merge(flat)  # `merge` auto-handles inserts/updates
            new_price = Price(flat_id=flat.flat_id, price=price)
            db.add(new_price)
            await db.flush()


async def flat_exists(flat_id: str, price: int) -> bool:
    """Check if a flat with the given id and price exists in the database."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Price).where(
            Price.flat_id == flat_id,
            Price.price == price
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None


async def add_favorite(flat_id: str, user_id: str) -> bool:
    """Add a favorite if it does not exist. Returns True if added, False if already exists."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(
            Favourite.flat_id == flat_id, Favourite.user_id == user_id
        )
        result = await db.execute(query)

        if result.scalars().first():
            return False

        new_fav = Favourite(flat_id=flat_id, user_id=user_id)
        db.add(new_fav)
        await db.commit()
        return True


async def remove_favorite(flat_id: str, user_id: str) -> bool:
    """Remove a flat from the user's favorites. Returns True if deleted, False if not found."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(
            Favourite.flat_id == flat_id, Favourite.user_id == user_id
        )
        result = await db.execute(query)
        fav = result.scalars().first()

        if not fav:
            return False

        await db.delete(fav)
        await db.commit()
        return True


async def find_favorite(flat_id: str, user_id: str) -> Favourite | None:
    """Check if a flat is in the user's favorites."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(
            Favourite.flat_id == flat_id, Favourite.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalars().first()


async def get_favourites(user_id: str) -> list[Favourite]:
    """Get all favorites for a user."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(Favourite.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all()
