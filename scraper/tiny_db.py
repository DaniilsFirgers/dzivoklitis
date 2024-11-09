from tinydb import TinyDB, Query
from datetime import datetime, timedelta


class FlatsTinyDb:
    def __init__(self, db_name, to_delete_interval=30):
        """Initialize the database."""
        self.db = TinyDB(f"{db_name}.json")
        self.table = self.db.table(db_name)
        self.to_delete_interval = to_delete_interval

    def insert(self, key, timestamp):
        """
        Insert a key-value pair into the database.
        :param key: Unique key (ID).
        :param timestamp: Timestamp in milliseconds.
        """
        if not self.exists(key):
            self.table.insert({'id': key, 'timestamp': timestamp})

    def delete_older_than_one_month(self):
        """
        Delete records older than one month.
        """
        one_month_ago = datetime.now() - timedelta(days=self.to_delete_interval)
        cutoff_timestamp = int(one_month_ago.timestamp()
                               * 1000)  # Convert to milliseconds

        self.table.remove(Query().timestamp < cutoff_timestamp)

    def exists(self, key):
        """
        Check if a record with a certain key exists.
        :param key: Key to check.
        :return: True if record exists, False otherwise.
        """
        return self.table.contains(Query().id == key)

    def close(self):
        """Close the database connection."""
        self.db.close()
