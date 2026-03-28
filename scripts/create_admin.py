"""
Create an admin user in the MySQL database.
Run: python scripts/create_admin.py
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymysql
from werkzeug.security import generate_password_hash

# Load config
try:
    from instance.config import (
        MYSQL_HOST, MYSQL_PORT, MYSQL_USER,
        MYSQL_PASSWORD, MYSQL_DATABASE
    )
except ImportError:
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'aqua_db')


def create_admin(username: str, password: str):
    """Insert a new admin with hashed password."""
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor
    )
    password_hash = generate_password_hash(password)
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO admins (username, password_hash) VALUES (%s, %s)',
            (username, password_hash)
        )
    conn.commit()
    conn.close()
    print(f'Admin user "{username}" created successfully.')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python scripts/create_admin.py <username> <password>')
        print('Example: python scripts/create_admin.py admin admin123')
        sys.exit(1)
    username = sys.argv[1]
    password = sys.argv[2]
    try:
        create_admin(username, password)
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)
