from fastapi import HTTPException
from psycopg2 import DataError, IntegrityError
from sqlalchemy.orm import Session
from backend.models.filter import Filter
from psycopg2.extras import NumericRange
from backend.schemas.filter import FilterCreate
from sqlalchemy.exc import SQLAlchemyError


def create_flats_filter(db: Session, filter: FilterCreate):
    try:
        #  TODO: need to check if submitted district is valid
        flats_filter = Filter(
            name=filter.name,
            district=filter.district,
            room_range=NumericRange(
                filter.rooms_range[0], filter.rooms_range[1], bounds='[]'),
            price_range=NumericRange(
                filter.price_range[0], filter.price_range[1], bounds='[]'),
            area_range=NumericRange(
                filter.area_range[0], filter.area_range[1], bounds='[]'),
            floor_range=NumericRange(
                filter.floor_range[0], filter.floor_range[1], bounds='[]'),
            tg_user_id=filter.tg_user_id
        )
        db.add(flats_filter)
        db.commit()
        db.refresh(flats_filter)
        return flats_filter

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User does not exist")
    except DataError as e:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Invalid data format")

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Internal server error")


def get_filters_by_user_id(db: Session, tg_user_id: int):
    try:
        if not isinstance(tg_user_id, int) or tg_user_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid user ID")

        filters = db.query(Filter).filter(
            Filter.tg_user_id == tg_user_id).all()

        return filters

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred")

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Unexpected error occurred")
