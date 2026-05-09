import mysql.connector
import sys

def test_connection():
    try:
        print("Attempting to connect to MySQL...")
        # Adjust these credentials if your setup is different!
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",  
            database="kbn_housekeeping" 
        )
        print("✅ SUCCESS! Connected to the 'kbn_housekeeping' database.")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bookings")
        count = cursor.fetchone()[0]
        print(f"📊 There are currently {count} bookings saved in the table.")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print("❌ FAILED TO CONNECT TO MYSQL!")
        print(f"Error Message: {err}")
        print("\nCommon fixes:")
        print("1. Did you create the database 'kbn_housekeeping' and the 'bookings' table?")
        print("2. Is your MySQL server actually running?")
        print("3. Do you have a password set for the 'root' user? (If yes, update the password field in this script and app.py)")
        
if __name__ == "__main__":
    test_connection()
