from sqlalchemy import BigInteger,  Column, ForeignKey, Index, Integer,  String, UniqueConstraint
from scraper.database.postgres import postgres_instance
from sqlalchemy.orm import relationship


class Favourite(postgres_instance.Base):
    __tablename__ = "favourites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flat_id = Column(String(255), ForeignKey(
        "flats.flat_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

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
