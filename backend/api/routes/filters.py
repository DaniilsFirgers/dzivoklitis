from typing import List
from fastapi import APIRouter, Depends, Query
from backend.schemas.filter import FilterCreate, FilterResponse
from backend.services.filter_service import create_flat_filter, get_filters_by_user_id
from backend.database.postgres import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/", response_model=List[FilterResponse])
def get_filters(tg_user_id: int = Query(...), db: Session = Depends(get_db)):
    """Get all flats filters for a user"""
    return get_filters_by_user_id(db, tg_user_id)


@router.post("/", response_model=FilterResponse)
def create_flat(filter: FilterCreate, db: Session = Depends(get_db)):
    """Create a new flats filter"""
    return create_flat_filter(db, filter)
