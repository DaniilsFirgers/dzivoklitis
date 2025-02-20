from enum import Enum
from sqlalchemy import Column, String, Integer, SmallInteger, DECIMAL, ForeignKey, Text, TIMESTAMP,  func
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from scraper.database.postgres import postgres_instance


class Type(Enum):
    FLATS = "flats"
    PRICES = "prices"
    FAVOURITES = "favourites"


class Flat(postgres_instance.Base):
    __tablename__ = Type.FLATS.value

    flat_id = Column(String(255), primary_key=True)
    source = Column(String(30), nullable=False)
    deal_type = Column(String(30), nullable=False)
    url = Column(Text, nullable=False)
    district = Column(String(100), nullable=False)
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
    prices = relationship("Price", back_populates="flat",
                          cascade="all, delete")

    # Relationship with favourites table
    favourites = relationship(
        "Favourite", back_populates="flat", cascade="all, delete")


class Price(postgres_instance.Base):
    __tablename__ = Type.PRICES.value

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(String(255), ForeignKey(
        "flats.flat_id", ondelete="CASCADE"), nullable=False)
    price = Column(Integer, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(
    ), nullable=False)

    # Relationship back to Flat
    flat = relationship("Flat", back_populates="prices")


class Favourite(postgres_instance.Base):
    __tablename__ = Type.FAVOURITES.value

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(String(255), ForeignKey(
        "flats.flat_id", ondelete="CASCADE"), nullable=False)

    user_id = Column(Integer, nullable=False)

    # Relationship back to Flat
    flat = relationship("Flat", back_populates="favourites")
