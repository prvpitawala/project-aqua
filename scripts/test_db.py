"""
Test MySQL database connection.
Run: python scripts/test_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models import get_db_connection
    conn = get_db_connection()
    conn.close()
    print("SUCCESS: Database connection works!")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
