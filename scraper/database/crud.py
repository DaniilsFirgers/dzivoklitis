from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from sqlalchemy import cast
from sqlalchemy.dialects.postgresql import NUMRANGE

from scraper.database.models.flat import Flat
from scraper.database.models.price import Price
from scraper.database.models.favorite import Favourite
from scraper.database.models.user import User
from scraper.database.models.filter import Filter
from scraper.database.postgres import postgres_instance
from scraper.schemas.shared import DealType


async def upsert_flat(flat: Flat, price: int) -> None:
    """Insert or update a flat and add its price."""
    async with postgres_instance.SessionLocal() as db:
        async with db.begin():  # Auto rollback on failure
            await db.merge(flat)  # `merge` auto-handles inserts/updates
            new_price = Price(flat_id=flat.flat_id,
                              price=price, updated_at=flat.created_at)
            db.add(new_price)
            await db.commit()


async def upsert_price(flat_id: str, price: int, updated_at: datetime) -> None:
    """Insert or update a price for a flat."""
    async with postgres_instance.SessionLocal() as db:
        async with db.begin():
            new_price = Price(flat_id=flat_id, price=price,
                              updated_at=updated_at)
            db.add(new_price)
            await db.commit()


async def flat_exists(flat_id: str, price: int) -> bool:
    """Check if a flat with the given id and price exists in the database."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Price).where(
            Price.flat_id == flat_id,
            Price.price == price
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None


async def get_flat(flat_id: str) -> Flat | None:
    """Get a flat by its id together with its prices."""
    async with postgres_instance.SessionLocal() as db:
        query = (
            select(Flat)
            .options(joinedload(Flat.prices))
            .where(Flat.flat_id == flat_id)
        )
        result = await db.execute(query)
        return result.unique().scalar_one_or_none()


async def add_favorite(flat_id: str, tg_user_id: int) -> bool:
    """Add a favorite if it does not exist. Returns True if added, False if already exists."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(
            Favourite.flat_id == flat_id, Favourite.tg_user_id == tg_user_id
        )
        result = await db.execute(query)

        if result.scalars().first():
            return False

        new_fav = Favourite(flat_id=flat_id, tg_user_id=tg_user_id)
        db.add(new_fav)
        await db.commit()
        return True


async def remove_favorite(flat_id: str, tg_user_id: str) -> bool:
    """Remove a flat from the user's favorites. Returns True if deleted, False if not found."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(
            Favourite.flat_id == flat_id, Favourite.tg_user_id == tg_user_id
        )
        result = await db.execute(query)
        fav = result.scalars().first()

        if not fav:
            return False

        await db.delete(fav)
        await db.commit()
        return True


async def find_favorite(flat_id: str, tg_user_id: str) -> Favourite | None:
    """Check if a flat is in the user's favorites."""
    async with postgres_instance.SessionLocal() as db:
        query = select(Favourite).where(
            Favourite.flat_id == flat_id, Favourite.tg_user_id == tg_user_id
        )
        result = await db.execute(query)
        return result.scalars().first()


async def get_favourites(tg_user_id: int) -> list[Flat]:
    """Get all favorites for a user."""
    async with postgres_instance.SessionLocal() as db:
        query = (
            select(Flat)
            .join(Favourite, Favourite.flat_id == Flat.flat_id)
            .options(joinedload(Flat.prices))
            .where(Favourite.tg_user_id == tg_user_id)
        )
        result = await db.execute(query)
        return result.unique().scalars().all()


async def get_users() -> list[User]:
    """Get all users."""
    async with postgres_instance.SessionLocal() as db:
        query = select(User)
        result = await db.execute(query)
        return result.scalars().all()


async def get_matching_filters_tg_user_ids(
    city: str,
    district: str,
    deal_type: DealType,
    rooms: int,
    price: int,
    area: int,
    floor: int
) -> list[int]:
    """Fetch telegram user ids for active filters that match the given city, district, deal type, and range conditions."""

    async with postgres_instance.SessionLocal() as db:  # Open async session
        query = select(Filter.tg_user_id).where(
            Filter.city == city,
            Filter.district == district,
            Filter.is_active == True,
            Filter.deal_type == deal_type.value,
            # ✅ Check if `rooms` is inside `room_range`
            Filter.room_range.op("@>")(cast((rooms, rooms), NUMRANGE)),
            # ✅ Check if `price` is inside `price_range`
            Filter.price_range.op("@>")(cast((price, price), NUMRANGE)),
            # ✅ Check if `area` is inside `area_range`
            Filter.area_range.op("@>")(cast((area, area), NUMRANGE)),
            # ✅ Check if `floor` is inside `floor_range`
            Filter.floor_range.op("@>")(cast((floor, floor), NUMRANGE))
        )

        result = await db.execute(query)
        return result.scalars().all()
