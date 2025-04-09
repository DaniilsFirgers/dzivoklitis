from sqlalchemy import TIMESTAMP, CheckConstraint, Column, ForeignKey, Index, Integer, String,  func
from shared_models.base import Base
from sqlalchemy.orm import relationship


class Price(Base):
    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(String(255), ForeignKey(
        "flats.flat_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
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
