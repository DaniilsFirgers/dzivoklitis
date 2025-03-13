from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Integer, String, func
from backend.database.postgres import Base
from sqlalchemy.dialects.postgresql import NUMRANGE
from sqlalchemy.orm import relationship


class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
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
