from sqlalchemy import TIMESTAMP, Column, Integer, String, func
from backend.database.postgres import Base
from sqlalchemy.dialects.postgresql import NUMRANGE


class Filter(Base):
    __tablename__ = "filters"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    rooms = Column(Integer, nullable=False)
    price_range = Column(NUMRANGE, nullable=False)
    area_range = Column(NUMRANGE, nullable=False)
    floor_range = Column(NUMRANGE, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), nullable=False)
