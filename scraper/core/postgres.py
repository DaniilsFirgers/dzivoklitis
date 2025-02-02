from enum import Enum
from typing import List
import psycopg2
from scraper.flat import Flat
from scraper.utils.logger import logger
from scraper.utils.meta import SingletonMeta
import os


class Type(Enum):
    FLATS = "flats"
    PRICES = "prices"
    FAVOURITES = "favourites"


class Postgres(metaclass=SingletonMeta):
    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", 5432)
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.database = os.getenv("POSTGRES_DB", "flats")
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

    def exists_with_id(self, flat_id: str, table: Type) -> bool:
        """Check if a flat with a given id exists in the database.
        """
        query = f"SELECT * FROM {table.value} WHERE flat_id = %s"
        self.cursor.execute(query, (flat_id,))
        return bool(self.cursor.fetchone())

    def exists_with_id_and_price(self, flat_id: str, price: float, tolerance: float = 0.1) -> bool:
        """Check if a flat with a given id and price (per m^2) exists in the database.
        The price is checked with a tolerance to handle floating-point precision issues.
        """
        query = f"""
            SELECT 1 FROM {Type.FLATS.value} f
            JOIN {Type.PRICES.value} p ON f.flat_id = p.flat_id
            WHERE f.flat_id = %s AND ABS(p.price - %s) < %s
            LIMIT 1;
            """
        self.cursor.execute(query, (flat_id, price, tolerance))
        return bool(self.cursor.fetchone())

    def add_or_update(self, flat: Flat):
        """Checks if a flat with the same id exists in the database.
        If it does, it updates the price and adds a new record to the flat_updates table.
        If it doesn't, it adds the flat to the flats table."""
        try:
            if self.exists_with_id(flat.id, Type.FLATS):
                print(
                    f"Flat with id {flat.id} already exists in the database. Updating the price!!!!")
                update_flat_query = f"""UPDATE {Type.FLATS.value} SET url = %s
                    WHERE flat_id = %s;"""
                self.cursor.execute(update_flat_query, (flat.url, flat.id))

                insert_price_query = f"""INSERT INTO {Type.PRICES.value} (flat_id, price)
                    VALUES (%s, %s);"""
                self.cursor.execute(insert_price_query,
                                    (flat.id, flat.price))
            else:
                query = f"""INSERT INTO {Type.FLATS.value} (flat_id, source, deal_type, url, district, street, rooms, area, floor, floors_total, series, location, image_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(COALESCE(%s, 0), COALESCE(%s, 0)), 4326), %s)"""
                self.cursor.execute(query, (flat.id, flat.source.value, flat.deal_type, flat.url, flat.district, flat.street,
                                    flat.rooms, flat.area, flat.floor, flat.floors_total, flat.series, flat.longitude, flat.latitude, flat.image_data))

                query = f"""INSERT INTO {Type.PRICES.value} (flat_id, price) VALUES (%s, %s)"""
                self.cursor.execute(query, (flat.id, flat.price))
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise ValueError(f"Error adding a flat to the database: {e}")

    def add_to_favourites(self, flat_id: str):
        """Add a flat to the favourites table."""
        try:
            query = f"INSERT INTO {Type.FAVOURITES.value} (flat_id) VALUES (%s)"
            self.cursor.execute(query, (flat_id,))
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            raise ValueError(f"Error adding a flat to favourites: {e}")

    def delete(self, flat_id: str, table: Type):
        """Delete a flat from the favourites table."""
        try:
            query = f"DELETE FROM {table.value} WHERE flat_id = %s"
            self.cursor.execute(query, (flat_id,))
            self.conn.commit()
            logger.info(f"Deleted a flat with id {flat_id} from the database.")
        except psycopg2.Error as e:
            self.conn.rollback()
            raise ValueError(f"Error deleting a flat from favourites: {e}")

    def get_favourites(self) -> List[tuple]:
        """Get all flats from the favourites table along with the latest price per m2."""
        try:
            # Query to get favourites and their latest price from price_updates
            query = f"""
            SELECT 
                f.flat_id, 
                f.source, 
                f.deal_type,
                f.url, 
                f.district, 
                f.street, 
                f.rooms, 
                f.floors_total, 
                f.floor, 
                f.area, 
                f.series, 
                ST_X(f.location) AS longitude, 
                ST_Y(f.location) AS latitude, 
                f.image_data, 
                p.price
            FROM {Type.FAVOURITES.value} ff
            INNER JOIN {Type.FLATS.value} f ON ff.flat_id = f.flat_id
            LEFT JOIN LATERAL (
                SELECT price
                FROM {Type.PRICES.value} p
                WHERE p.flat_id = f.flat_id
                ORDER BY p.updated_at DESC
                LIMIT 1
            ) p ON true;
            """

            # Execute the query
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
