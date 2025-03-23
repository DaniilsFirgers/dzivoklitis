from typing import List
from geoalchemy2 import Geometry
from sqlalchemy import DECIMAL, TIMESTAMP, CheckConstraint, Column, Index, SmallInteger, String, Text, func
from scraper.database.postgres import postgres_instance
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import relationship, Mapped
from scraper.database.models.price import Price
from scraper.database.models.favorite import Favourite


class Flat(postgres_instance.Base):
    __tablename__ = "flats"

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
