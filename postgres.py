import pandas as pd
import psycopg2
import os
import traceback
from dotenv import load_dotenv


load_dotenv()
db_connection_string = os.getenv("DB_CONN_STR")


class DB:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
        self.connect()

    def connect(self):
        if not self.connection:
            try:
                self.connection = psycopg2.connect(self.connection_string)
            except (Exception, psycopg2.Error) as error:
                print("PostgreSQL error:", error)
        return self.connection

    def __enter__(self):
        return self

    def psql_to_dataframe(self, query, column_names):
        data = []
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            cursor.close()
        except (Exception, psycopg2.Error) as error:
            print("PostgreSQL error:", error)
        df = pd.DataFrame(data, columns=column_names)
        return df

    def close(self):
        if self.connection:
            self.connection.close()

    def __exit__(self, exc_type, exc_value, tb):
        self.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through
        return True


if __name__ == "__main__":
    with DB(db_connection_string) as db:
        conn = db.connect()
        cur = conn.cursor()
        cur.execute('SELECT version()')
        print(cur.fetchone())
        cur.close()

