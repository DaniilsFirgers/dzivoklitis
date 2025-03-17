from enum import Enum
from typing import List
from sqlalchemy import VARCHAR, BigInteger, Column, String, Integer, SmallInteger, DECIMAL, ForeignKey, Text, TIMESTAMP,  func
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship, Mapped
from geoalchemy2 import Geometry
from sqlalchemy import Index
from scraper.database.postgres import postgres_instance
from sqlalchemy import CheckConstraint, UniqueConstraint


class TableType(Enum):
    FLATS = "flats"
    PRICES = "prices"
    FAVOURITES = "favourites"
    USERS = "users"


class Flat(postgres_instance.Base):
    __tablename__ = TableType.FLATS.value

    flat_id = Column(String(255), primary_key=True)
    source = Column(String(30), nullable=False)
    deal_type = Column(String(30), nullable=False)
    url = Column(Text, nullable=False)
    district = Column(String(100), nullable=False)
    city = Column(String(50), nullable=True)
    street = Column(String(150), nullable=False)
    rooms = Column(SmallInteger, nullable=False)
    floors_total = Column(SmallInteger, nullable=False)
    floor = Column(SmallInteger, nullable=False)
    area = Column(DECIMAL(5, 2), nullable=False)
    series = Column(Text, nullable=False)
    # Geospatial point (longitude, latitude)
    location = Column(Geometry("POINT", srid=4326))
    image_data = Column(BYTEA, default=b"")  # Binary data for images
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now())

    # Relationship with prices table
    prices: Mapped[List["Price"]] = relationship("Price", back_populates="flat",
                                                 cascade="all, delete")

    # Relationship with favourites table
    favourites: Mapped[List["Favourite"]] = relationship(
        "Favourite", back_populates="flat", cascade="all, delete")

    __table_args__ = (
        Index("idx_flat_location", location, postgresql_using="GIST"),
        CheckConstraint("floor <= floors_total",
                        name="floor_vs_total_floor_check"),
        CheckConstraint("rooms > 0", name="rooms_check"),
        CheckConstraint("area > 0", name="area_check"),
        CheckConstraint("floors_total > 0", name="floors_total_check"),
        CheckConstraint("floor > 0", name="floor_check"),
    )


class Price(postgres_instance.Base):
    __tablename__ = TableType.PRICES.value

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(String(255), ForeignKey(
        "flats.flat_id", ondelete="CASCADE"), nullable=False)
    price = Column(Integer, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(
    ), nullable=False)

    # Relationship back to Flat
    flat = relationship("Flat", back_populates="prices")

    __table_args__ = (
        Index("idx_price_flat_id", flat_id),
        Index("idx_price_flat_id_price", flat_id, price),
        CheckConstraint("price > 0", name="price_check"),
    )


class Favourite(postgres_instance.Base):
    __tablename__ = TableType.FAVOURITES.value

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(String(255), ForeignKey(
        "flats.flat_id", ondelete="CASCADE"), nullable=False)

    tg_user_id = Column(BigInteger, ForeignKey(
        "users.tg_user_id", ondelete="CASCADE"),  nullable=False, )

    # Relationship back to Flat
    flat = relationship("Flat", back_populates="favourites")

    __table_args__ = (
        Index("idx_fav_flat_id", flat_id),
        Index("idx_fav_tg_user_id", tg_user_id),
        UniqueConstraint("flat_id", "tg_user_id",
                         name="uq_fav_flat_id_tg_user_id"),
    )


class User(postgres_instance.Base):
    __tablename__ = TableType.USERS.value

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(30), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_user_tg_user_id", tg_user_id),
        UniqueConstraint("tg_user_id", name="uq_user_tg_user_id"),
    )
