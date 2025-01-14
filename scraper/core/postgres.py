from enum import Enum
from typing import List
import psycopg2
from scraper.flat import Flat
from scraper.utils.logger import logger
from scraper.utils.meta import SingletonMeta


class Table(Enum):
    FLATS = "flats"
    FLAT_UPDATES = "flat_updates"
    FAVOURITE_FLATS = "favourite_flats"


class Postgres(metaclass=SingletonMeta):
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish a connection to the database and create a cursor."""
        if self.conn and self.cursor:
            return
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.conn.cursor()
            logger.info("Connected to the database.")
        except psycopg2.Error as e:
            logger.error(f"Error connecting to the database: {e}")

    def check_if_exists(self, flat_id: str, table: Table) -> bool:
        """Check if a flat with a given id exists in the database."""
        query = f"SELECT * FROM {table.value} WHERE flat_id = %s"
        self.cursor.execute(query, (flat_id,))
        return bool(self.cursor.fetchone())

    def add(self, flat: Flat):
        """Add a flat to the database."""
        try:
            query = """INSERT INTO flats (flat_id, source, link, district, street, price_per_m2, rooms, area, floor, floors_total, series)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            self.cursor.execute(query, (flat.id, flat.source.value, flat.link, flat.district, flat.street, flat.price_per_m2,
                                flat.rooms, flat.m2, flat.floor, flat.last_floor, flat.series))
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise ValueError(f"Error adding a flat to the database: {e}")

    def add_to_favourites(self, flat_id: str):
        """Add a flat to the favourites table."""
        try:
            query = "INSERT INTO favourite_flats (flat_id) VALUES (%s)"
            self.cursor.execute(query, (flat_id,))
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise ValueError(f"Error adding a flat to favourites: {e}")

    def delete(self, flat_id: str, table: Table):
        """Delete a flat from the favourites table."""
        try:
            query = f"DELETE FROM {table.value} WHERE flat_id = %s"
            self.cursor.execute(query, (flat_id,))
            self.conn.commit()
            logger.info(f"Deleted a flat with id {flat_id} from the database.")
        except psycopg2.Error as e:
            self.conn.rollback()
            raise ValueError(f"Error deleting a flat from favourites: {e}")

    def get_favourites(self) -> List[Flat]:
        """Get all flats from the favourites table."""
        try:
            query = "SELECT * FROM favourite_flats"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Error getting favourites: {e}")

    def close(self):
        """Close the cursor and connection."""
        if not self.conn or not self.cursor:
            return
        try:
            self.cursor.close()
            self.conn.close()
            logger.info("Closed the connection.")
        except psycopg2.Error as e:
            logger.error(f"Error closing the connection: {e}")
