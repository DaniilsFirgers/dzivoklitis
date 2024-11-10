import time
import redis
from tinydb import TinyDB, Query
from datetime import datetime, timedelta

from scraper.flat import Flat


class FlatsTinyDb:
    def __init__(self, parsed_db_name, to_delete_interval=30):
        """Initialize the database."""
        self.db = TinyDB(f"{parsed_db_name}.json")
        self.parsed_db = self.db.table("parsed")
        self.favorites_db = self.db.table("favorites")
        self.to_delete_interval = to_delete_interval

    def get(self, key: str, db_name: str = "parsed"):
        """
        Get flat info from the database by its key.
        """
        if db_name == "parsed":
            return self.parsed_db.get(Query().id == key)
        elif db_name == "favorites":
            return self.favorites_db.get(Query().id == key)
        else:
            raise ValueError(
                "Invalid db_name. Expected 'parsed' or 'favorites'.")

    def insert(self, key: str, flat: Flat, db_name: str = "parsed"):
        """
        Insert flat info to the database together with its id and timestamp
        """
        timestamp = int(time.time() * 1000)

        if isinstance(flat, dict):
            flat = Flat(**flat)

        flat_obj = {
            'id': key,
            'timestamp': timestamp,
            'flat': flat.to_dict()
        }

        if db_name == "parsed" and not self.exists(key):
            self.parsed_db.insert(flat_obj)
        elif db_name == "favorites" and not self.exists(key, "favorites"):
            self.favorites_db.insert(flat_obj)

    def delete_old_ads(self):
        """
        Delete records older than 'x' period specified in donfig file.
        """
        one_month_ago = datetime.now() - timedelta(days=self.to_delete_interval)
        cutoff_timestamp = int(one_month_ago.timestamp()
                               * 1000)  # Convert to milliseconds

        self.parsed_db.remove(Query().timestamp < cutoff_timestamp)

    def exists(self, key: str, db_name: str = "parsed"):
        """
        Check if a flat record with a certain key exists.
        """
        if db_name == "parsed":
            return self.parsed_db.get(Query().id == key)
        elif db_name == "favorites":
            return self.favorites_db.get(Query().id == key)
        else:
            raise ValueError(
                "Invalid db_name. Expected 'parsed' or 'favorites'.")

    def close(self):
        """Close the database connection."""
        self.db.close()
