from sqlalchemy import TIMESTAMP, BigInteger,  Column,  Index, Integer, String, UniqueConstraint, func
from shared_models.base import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_user_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(30), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), onupdate=func.now(), nullable=False)
    filters = relationship("Filter", back_populates="user",
                           cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_user_tg_user_id", tg_user_id),
        UniqueConstraint("tg_user_id", name="uq_user_tg_user_id"),
    )
