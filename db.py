import pyodbc

# SQL Server connection string
conn_str = (
    r"DRIVER={ODBC Driver 17 for SQL Server};"
    r"SERVER=LAPTOP-8LVDKS7P\SQLEXPRESS;"  # Replace this with your actual SQL Server instance
    r"DATABASE=TextileShopDB;"
    r"Trusted_Connection=yes;"
)


def get_db_connection():
    try:
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
