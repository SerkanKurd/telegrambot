from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Optional
import cities


_DB_PATH = Path(__file__).resolve().with_name("mydb.db")


def _get_connection() -> sqlite3.Connection:
    """Return a SQLite connection configured for row access via column names."""
    connection = sqlite3.connect(_DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_cursor(commit: bool = False):
    """Yield a cursor and commit/rollback according to the context outcome."""
    connection = _get_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def ensure_user_table() -> None:
    """Create the users table when it does not already exist."""
    ddl = []
    ddl.append("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username VARCHAR(50),
        firstname VARCHAR(50),
        lastname VARCHAR(50),
        isbot BOOLEAN,
        city VARCHAR(50),
        takeoff VARCHAR(100),
        lat DECIMAL(9,6),
        lon DECIMAL(9,6),
        forcast_city VARCHAR(50),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );""")
    ddl.append("""
    CREATE TABLE IF NOT EXISTS cities (
    code INT PRIMARY KEY,
    name VARCHAR(50),
    lat DECIMAL(9,6),
    lon DECIMAL(9,6)
    );
    """)
    with get_cursor(commit=True) as cursor:
        for statement in ddl:
            cursor.execute(statement)


def create_user(user_data) -> Optional[int]:
    """Insert a user row or refresh basic fields when the user already exists."""
    query = (
        "INSERT INTO users (id, username, firstname, lastname, isbot) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET "
        "username=excluded.username, "
        "firstname=excluded.firstname, "
        "lastname=excluded.lastname, "
        "isbot=excluded.isbot; "
    )
    with get_cursor(commit=True) as cursor:
        cursor.execute(
            query, (
                user_data.id,
                user_data.username,
                user_data.first_name,
                user_data.last_name,
                bool(user_data.is_bot)),
        )
        return cursor.lastrowid


def list_users() -> Iterable[Dict[str, object]]:
    query = "SELECT id, username, firstname, lastname, isbot, city, takeoff, created_at FROM users ORDER BY created_at;"
    with get_cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_user(user_id: int) -> Optional[dict]:
    query = (
        "SELECT * "
        "FROM users WHERE id = ?;"
    )
    try:
        with get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(e)
        return None


def get_user_by_username(username: str) -> Optional[Dict[str, object]]:
    query = (
        "SELECT id, username, firstname, lastname, isbot, city, takeoff, created_at "
        "FROM users WHERE username = ?;"
    )
    with get_cursor() as cursor:
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_user(
    user_data,
    *,
    takeoff: Optional[str] = None,
    city: Optional[str] = None,
    lat: Optional[int] = None,
    lon: Optional[int] = None,
    forcast_city: Optional[str] = None
) -> bool:
    if get_user(user_data.id) is None:
        create_user(user_data)
    fields = []
    params = []
    city = cities.find_city(lat, lon) if lat and lon else None
    if user_data.username is not None:
        fields.append("username = ?")
        params.append(user_data.username)
    if user_data.first_name is not None:
        fields.append("firstname = ?")
        params.append(user_data.first_name)
    if user_data.last_name is not None:
        fields.append("lastname = ?")
        params.append(user_data.last_name)
    if user_data.is_bot is not None:
        fields.append("isbot = ?")
        params.append(int(user_data.is_bot))
    if takeoff is not None:
        fields.append("takeoff = ?")
        params.append(takeoff)
    if city is not None:
        fields.append("city = ?")
        params.append(city)
    if lat is not None:
        fields.append("lat = ?")
        params.append(lat)
    if lon is not None:
        fields.append("lon = ?")
        params.append(lon)
    if forcast_city is not None:
        fields.append("forcast_city = ?")
        params.append(forcast_city)
    if not fields:
        return False

    params.append(user_data.id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?;"
    with get_cursor(commit=True) as cursor:
        cursor.execute(query, params)
        return cursor.rowcount > 0


def delete_user(user_id: int) -> bool:
    """Remove a user record by id. Return True when a row was deleted."""
    query = "DELETE FROM users WHERE id = ?;"
    with get_cursor(commit=True) as cursor:
        cursor.execute(query, (user_id,))
        return cursor.rowcount > 0


def get_city_location(city_name: str) -> Optional[tuple]:
    query = "SELECT lat, lon FROM cities WHERE name = ?;"
    with get_cursor() as cursor:
        cursor.execute(query, (city_name,))
        row = cursor.fetchone()
        return (row["lat"], row["lon"]) if row else None


def get_is_valid_city(city_name: str) -> str:
    city_name = city_name.replace("I", "ı").replace("İ", "i").lower()
    city_name = city_name[0].replace("ı", "I").replace("i", "İ").upper() + city_name[1:]
    print((city_name))
    query = "SELECT name FROM cities WHERE name = ?;"
    with get_cursor() as cursor:
        cursor.execute(query, (city_name,))
        row = cursor.fetchall()[0]
        if len(row) > 0:
            return row["name"]
        return ""


if __name__ == "__main__":
    # ensure_user_table()
    # print(get_user(8341631255))
    # print(get_user(1111131255))
    # print(get_city_location("Ankara"))
    print(get_is_valid_city("IĞDIR"))
