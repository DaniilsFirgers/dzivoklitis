from fastapi import HTTPException
from sqlalchemy.orm import Session
from shared_models import Favourite
from sqlalchemy.exc import SQLAlchemyError


def get_user_favourites(db: Session, tg_user_id: int):
    try:
        if not isinstance(tg_user_id, int) or tg_user_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        favourites = db.query(Favourite).filter(
            Favourite.tg_user_id == tg_user_id).all()

        return favourites
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Database error occurred")
