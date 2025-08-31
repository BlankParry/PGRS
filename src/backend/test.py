import pymysql

def test_db_connection():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='1234',
            database='complaint_system',
            port=3306
        )
        print("Database connection successful!")
        connection.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_db_connection() 