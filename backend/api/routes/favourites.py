from typing import List
from fastapi import APIRouter, Depends, Query
from backend.schemas.filter import FilterResponse
from backend.services.favourite_service import get_user_favourites
from backend.database.postgres import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=List[FilterResponse])
def get_favourites(tg_user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get all favourites for a user"""
    return get_user_favourites(db, tg_user_id)
