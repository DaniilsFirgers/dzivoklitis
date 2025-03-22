from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String,  func
from scraper.database.postgres import postgres_instance
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import NUMRANGE


class Filter(postgres_instance.Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
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
