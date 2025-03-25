from sqlalchemy import TIMESTAMP, BigInteger, Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, String, func
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
    tg_user_id = Column(BigInteger, ForeignKey(
        "users.tg_user_id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False
                        )

    user = relationship("User", back_populates="filters")

    __table_args__ = (
        # GiST index for range fields
        Index(
            "idx_filter_gist",
            room_range,
            price_range,
            area_range,
            floor_range,
            postgresql_using="gist",
        ),
        # BTREE index for non-range fields like `is_active`, `city`, `district`, and `deal_type`
        Index("idx_filter_btree", is_active, city, district, deal_type),
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
