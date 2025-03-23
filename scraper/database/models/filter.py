from sqlalchemy import TIMESTAMP, BigInteger, CheckConstraint, Column, ForeignKey, Index, Integer, String, func
from scraper.database.postgres import postgres_instance
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import NUMRANGE


class Filter(postgres_instance.Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    deal_type = Column(String, nullable=False)
    city = Column(String, nullable=False)
    district = Column(String, nullable=False)
    room_range = Column(NUMRANGE, nullable=False)
    price_range = Column(NUMRANGE, nullable=False)
    area_range = Column(NUMRANGE, nullable=False)
    floor_range = Column(NUMRANGE, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), nullable=False)
    tg_user_id = Column(BigInteger, ForeignKey(
        "users.tg_user_id", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="filters")

    __table_args__ = (
        # We will query by city, deal type and ditrict and load only the filters that are relevant
        Index('idx_city_district', 'city', 'deal_type', 'district'),
        CheckConstraint("room_range IS NOT NULL", name="room_range_not_null"),
        CheckConstraint("price_range IS NOT NULL",
                        name="price_range_not_null"),
        CheckConstraint("area_range IS NOT NULL", name="area_range_not_null"),
        CheckConstraint("floor_range IS NOT NULL",
                        name="floor_range_not_null"),
        # Constraints for valid ranges (lower bound <= upper bound)
        CheckConstraint("lower(room_range) <= upper(room_range)",
                        name="check_room_range"),
        CheckConstraint("lower(price_range) <= upper(price_range)",
                        name="check_price_range"),
        CheckConstraint("lower(area_range) <= upper(area_range)",
                        name="check_area_range"),
        CheckConstraint("lower(floor_range) <= upper(floor_range)",
                        name="check_floor_range"),
    )
