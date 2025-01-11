import psycopg2
from scraper.utils.logger import logger
from scraper.utils.meta import SingletonMeta


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
            raise

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
            raise
